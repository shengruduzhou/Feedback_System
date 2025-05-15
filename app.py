from itertools import groupby
import matplotlib

matplotlib.use("Agg")
from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import mysql.connector
from mysql.connector import Error
import seaborn as sns
import hashlib
from scipy.stats import linregress


app = Flask(__name__, static_url_path="/static", static_folder="static")
app.config["UPLOAD_FOLDER"] = "./uploads"

# interface
# database connection
db_config = {
    "host": "localhost",
    "user": "teacher",
    "password": "teacher_password",
    "database": "attention_data",
    "port": 3306,
}
try:
    conn = mysql.connector.connect(**db_config)
    if conn and conn.is_connected():
        print("Database connection successful!")
    conn.close()
except mysql.connector.Error as error:
    print(f"Error: {error}")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_student_account(df):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for (class_id, student_id), _ in df.groupby(["classid", "studentid"]):
            studentUsername = f"student-{class_id}-{student_id}"
            studentPassword = f"{class_id}-{student_id}"
            hashed_password = hash_password(studentPassword)

            print(
                f"Inserting username: {studentUsername}, hashed_password: {hashed_password}"
            )

            query = """INSERT INTO user_accounts(username,password,user_type) VALUES(%s,%s,'student') ON DUPLICATE KEY UPDATE password = VALUES(password)"""
            values = (studentUsername, hashed_password)
            cursor.execute(query, values)

        conn.commit()
        print("Student account created successfully")
    except mysql.connector.Error as error:
        print(f"Error create student accounts:{error}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# insert data to database
def save_data_to_database(df):
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for _, row in df.iterrows():
            query = """INSERT INTO attention_data(studentid,classid,timestamp,attention_score,average_attention_score) VALUES(%s,%s,%s,%s,%s)"""
            values = (
                int(row["studentid"]),
                int(row["classid"]),
                row["timestamp"],
                float(row["attention_score"]),
                float(row["average_attention_score"]),
            )
            cursor.execute(query, values)

        conn.commit()
        print("Data saved to database successfully")
    except mysql.connector.Error as error:
        print(f"Error saving data to database:{error}")
        print(f"Error type:{type(error)}")
        print(f"Error args:{error.args}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def generate_plots(df):
    plot_paths = []
    for (class_id, student_id), group in df.groupby(["classid", "studentid"]):
        group = group.sort_values("timestamp")

        # set start
        start_time = group["timestamp"].dt.normalize() + pd.Timedelta(hours=9)
        group["time_from_start"] = (
            group["timestamp"] - start_time
        ).dt.total_seconds() / 3600

        # generate image
        plot_path = f"./static/class{class_id}_student{student_id}_plot.png"
        plt.figure(figsize=(10, 6), dpi=100)

        # personal_attention
        x_smooth = np.linspace(
            group["time_from_start"].min(), group["time_from_start"].max(), 300
        )
        spl = make_interp_spline(
            group["time_from_start"], group["attention_score"], k=3
        )
        y_smooth = spl(x_smooth)

        plt.plot(
            x_smooth,
            y_smooth,
            label="personal_attention",
            color="purple",
            alpha=0.7,
        )
        plt.fill_between(x_smooth, y_smooth, alpha=0.3, color="purple")

        # average_attention
        spl = make_interp_spline(
            group["time_from_start"], group["average_attention_score"], k=3
        )
        y_smooth = spl(x_smooth)

        plt.plot(
            x_smooth,
            y_smooth,
            label="average_attention",
            color="green",
            alpha=0.7,
        )
        plt.fill_between(x_smooth, y_smooth, alpha=0.3, color="green")

        slop, intercept, _, _, _ = linregress(
            group["time_from_start"], group["attention_score"]
        )
        trendline = slop * x_smooth + intercept
        plt.plot(x_smooth, trendline, label="trendline", color="red", linestyle="--")

        plt.title(f"Attention for class{class_id}-student{student_id}")
        plt.xlabel("TIME")
        plt.ylabel("ATTENTION")
        plt.legend()
        plt.ylim(0, 100)
        plt.savefig(plot_path, dpi=100)
        plt.close()

        plot_paths.append(
            {
                "class_id": int(class_id),
                "student_id": int(student_id),
                "plot_url": f"/static/class{class_id}_student{student_id}_plot.png",
            }
        )
    return plot_paths


# get account & data
@app.route("/get-students", methods=["GET"])
def get_students():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = "SELECT DISTINCT classid,studentid From attention_data ORDER BY classid,studentid"
        cursor.execute(query)
        students = cursor.fetchall()

        return jsonify({"students": students})
    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return jsonify({"error": "Failed to get students"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route("/get-data", methods=["GET"])
def get_data():
    student_id = request.args.get("student_id")
    class_id = request.args.get("class_id")

    if not student_id or not class_id:
        return jsonify({"error": "Missing student_id or class_id"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """SELECT timestamp,attention_score,average_attention_score FROM attention_data WHERE studentid = %s AND classid = %s ORDER BY timestamp"""
        cursor.execute(query, (student_id, class_id))
        data = cursor.fetchall()

        scores = [row["attention_score"] for row in data]
        
        if len(scores) < 2:
            feedback = "Not enough data to generate feedback"
            return jsonify({"data": data, "feedback": feedback})

        last_vs_previous = scores[-1] - scores[-2]
        
        metrics = defin_feedback_classification(scores)
        if metrics["trend_slope"] is not None:
            trend = "Attention is increasing" if metrics["trend_slope"] > 0 else "Attention is decreasing"
        else:
            trend = "Insufficient data for trend analysis"
        feedback = generate_feedback(metrics, trend, last_vs_previous)

        return jsonify({
            "mean": metrics["mean"],
            "std_dev": metrics["std_dev"],
            "trend_slope": metrics["trend_slope"],
            "last_vs_previous": last_vs_previous,
            "trend": trend,
            "feedback": feedback,
        })

    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return jsonify({"error": "Failed to get data"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route("/get-student-plots", methods=["GET"])
def get_student_plots():
    class_id = request.args.get("class_id")
    student_id = request.args.get("student_id")

    if not class_id or not student_id:
        return jsonify({"error": "Missing class_id or student_id"}), 400

    plot_url = f"/static/class{class_id}_student{student_id}_plot.png"
    return jsonify({"plot_url": plot_url})


# firstpage upload
@app.route("/")
def index():
    return render_template("data_upload.html")


# upload file
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith(".csv"):
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        return jsonify({"message": "File upload sucessfully", "filepath": filepath})
    else:
        return jsonify({"error": "Only CSV files are allowed"}), 400


# data-anaylsis and image-generate
student_accounts = {}  # save student username and password


@app.route("/analyze", methods=["POST"])
def analyze_file():
    conn = None
    try:
        data = request.get_json()
        filepath = data.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 400

        # useage Pandas load data
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.lower()

        # check data
        def required_columns_issubset(columns):
            required_columns = {
                "studentid",
                "classid",
                "timestamp",
                "attention_score",
                "average_attention_score",
            }
            return required_columns.issubset(columns)

        if not required_columns_issubset(df.columns):
            return (
                jsonify(
                    {
                        "error": "CSV file must include 'studentid','classid','timestamp','attention_score','average_attention_score''"
                    }
                ),
                400,
            )

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # data access
        df = df.dropna(
            subset=["timestamp", "attention_score", "average_attention_score"]
        )

        df = df[(df["attention_score"] >= 0) & (df["attention_score"] <= 100)]
        df = df[
            (df["average_attention_score"] >= 0)
            & (df["average_attention_score"] <= 100)
        ]

        save_data_to_database(df)
        create_student_account(df)
        plot_paths = generate_plots(df)

        return jsonify({"plots": plot_paths})

    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({"error": "An error occurred during analysis"}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# login-selection page
@app.route("/login-selection", methods=["GET", "POST"])
def login_selection():
    return render_template("login_selection.html")


# teacher-login page
@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "GET":
        return render_template("teacher_login.html")
    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        teacherUsername = data.get("teacher-username")
        teacherPassword = data.get("teacher-password")
        if teacherUsername == "teacher" and teacherPassword == "1":
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Invalid username or password"}), 400


# student-login page
@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    if request.method == "GET":
        return render_template("student_login.html")
    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        studentUsername = data.get("student-username")
        studentPassword = data.get("student-password")
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM user_accounts WHERE username = %s AND user_type = 'student'"
            cursor.execute(query, (studentUsername,))
            user = cursor.fetchone()

            print(f"Database user: {user}")
            print(f"Input hashed password: {hash_password(studentPassword)}")

            cursor.fetchall()

            if user and user["password"] == hash_password(studentPassword):
                _, class_id, student_id = studentUsername.split("-")
                return jsonify(
                    {"success": True, "class_id": class_id, "student_id": student_id}
                )
            else:
                return jsonify({"error": "Invalid username or password"}), 400
        except mysql.connector.Error as error:
            print(f"Database error: {error}")
            return jsonify({"error": "Invalid username or password"}), 400
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()


# teacher-dashboard page
@app.route("/teacher-dashboard", methods=["GET", "POST"])
def teacher_dashboard():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = "SELECT studentid,attention_score FROM attention_data ORDER BY timestamp DESC"
        cursor.execute(query)
        data = cursor.fetchall()

        student_data = {}
        for student_id, score in data:
            if student_id not in student_data:
                student_data[student_id] = []
            student_data[student_id].append(score)

        class_metrics = {}
        class_trends = {}
        feedback = {}

        for student_id, scores in student_data.items():
            stats = calculate_attention_stats(scores)

            if stats["error"]:
                feedback[student_id] = stats["error"]
                continue

            feedback[student_id] = generate_feedback(
                stats["metrics"], stats["trend"], stats["last_vs_previous"]
            )
            class_metrics[student_id] = stats["metrics"]
            class_trends[student_id] = stats["trend"]

        return render_template(
            "teacher_dashboard.html",
            user_type="teacher",
            class_metrics=class_metrics,
            class_trends=class_trends,
            feedback=feedback,
        )
    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return jsonify({"error": str(error)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route("/get-plots", methods=["GET"])
def get_plots():
    user_type = request.args.get("user_type")
    student_id = request.args.get("student_id", None)
    try:
        plots = []
        for filename in os.listdir("./static"):
            if filename.endswith("_plot.png"):
                parts = filename.split("_")
                cid = parts[0].replace("class", "")
                sid = parts[1].replace("student", "").replace(".png", "")
                if user_type == "teacher" or (
                    user_type == "student" and sid == student_id
                ):
                    plots.append(
                        {
                            "class_id": cid,
                            "student_id": sid,
                            "plot_url": f"/static/{filename}",
                        }
                    )
        print("Returning plots:", plots)
        return jsonify({"plots": plots})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to load plots"}), 500


# student-dashboard page
@app.route("/student-dashboard", methods=["GET", "POST"])
def student_dashboard():
    class_id = request.args.get("class_id")
    student_id = request.args.get("student_id")
    if not class_id or not student_id:
        return jsonify({"error": "Missing class_id or student_id"}), 400
    try:
        attention_scores = get_student_attention_scores(class_id, student_id)

        if not attention_scores:
            return (
                jsonify(
                    {
                        "error": "No attention data found for this student",
                        "class_id": class_id,
                        "student_id": student_id,
                    }
                ),
                404,
            )

        stats = calculate_attention_stats(attention_scores)
        if stats["error"]:
            return jsonify({"error": stats["error"]}), 400

        feedback = generate_feedback(
            stats["metrics"], stats["trend"], stats["last_vs_previous"]
        )

        return render_template(
            "student_dashboard.html",
            class_id=class_id,
            student_id=student_id,
            attention_scores=attention_scores,
            metrics=stats["metrics"],
            current_attention=attention_scores[-1],
            trend=stats["trend"],
            feedback=feedback,
        )
        
    except Exception as e:
        print(f"Error in student-dashboard: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/check-accounts", methods=["GET"])
def check_accounts():
    print("Accessing /check-accounts route")
    return jsonify(student_accounts)


# test database connection
def test_database_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print("Database connection successful")
        conn.close()
    except mysql.connector.Error as error:
        print(f"Database connection error: {error}")


# feedback
# feedback classification
def defin_feedback_classification(scores):
    """Calculate metrics for feedback classification."""
    mean_score = np.mean(scores)
    std_dev = np.std(scores)
    times = list(range(len(scores)))
    trend_slope = calculate_trend_slope(scores, times)

    return {
        "mean": mean_score,
        "std_dev": std_dev,
        "trend_slope": trend_slope,
    }


def classify_attention(score, mean, std_dev):
    if score < mean - std_dev:
        return "low attention"
    elif score > mean + std_dev:
        return "high attention"
    else:
        return "normal attention"


def analyze_attention_trend(attention_score):
    if len(attention_score) < 2:
        return "Not enough attention data"

    trend = np.polyfit(range(len(attention_score)), attention_score, 1)[0]

    if trend > 0:
        return "Attention is increasing"
    elif trend < 0:
        return "Attention is decreasing"
    else:
        return "Attention is stable"


@app.route("/updata-attention", methods=["GET", "POST"])
def updata_attention():
    """Updatas attention score and provides real-time feedback.Compares the latest attention score with the previous one and calculates trends."""
    data = request.json
    student_id = data.get("student_id")
    attention_score = data.get("attention_score")

    if not student_id or not attention_score is None:
        return jsonify({"error": "Missing student_id or attention_score"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = """INSERT INTO attention_data(studentid,timestamp,attention_score) VALUES(%s,NOW(),%s)"""
        cursor.execute(query, (student_id, attention_score))
        conn.commit()

        select_recent_query = """SELECT attention_score FROM attention_data WHERE studentid = %s ORDER BY timestamp DESC LIMIT 2"""
        cursor.execute(select_recent_query, (student_id,))
        recent_scores = [row[0] for row in cursor.fetchall()]

        select_all_query = (
            """SELECT attention_score FROM attention_data WHERE studentid = %s"""
        )
        cursor.execute(select_all_query, (student_id,))
        all_scores = [row[0] for row in cursor.fetchall()]

        if len(recent_scores) < 2:
            return (
                jsonify({"feedback": "Not enough attention data for comparison"}),
                400,
            )

        last_score = recent_scores[0]
        previous_score = recent_scores[1]
        last_vs_previous = last_score - previous_score
        metrics = defin_feedback_classification(all_scores)
        trend = analyze_attention_trend(all_scores)
        feedback = generate_feedback(metrics, trend, last_vs_previous)

        feedback = generate_feedback(
            metrics, trend, last_vs_previous, score_threshold=10, std_threshold=10
        )

        print(f"Generated feedback: {feedback}")

        return jsonify(
            {
                "lasi_score": last_score,
                "previous_score": previous_score,
                "mean": metrics["mean"],
                "std_dev": metrics["std_dev"],
                "trend": trend,
                "feedback": feedback,
            }
        )

    except mysql.connector.Error as error:
        return jsonify({"error": str(error)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_student_attention_scores(class_id, student_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = """SELECT attention_score FROM attention_data WHERE classid = %s AND studentid = %s ORDER BY timestamp ASC"""
        cursor.execute(query, (class_id, student_id))
        scores = [row[0] for row in cursor.fetchall()]
        print(
            f"Fetched attention scores for class_id={class_id}, student_id={student_id}: {scores}"
        )
        return scores
    except mysql.connector.Error as error:
        print(f"Error fetching attention score: {error}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def calculate_attention_stats(attention_scores):
    if len(attention_scores) < 2:
        return {
            "last_vs_previous": None,
            "trend": "Not enough data",
            "metrics": None,
            "error": "Not enough data for comparison",
        }

    last_score = attention_scores[-1]
    previous_score = attention_scores[-2]
    last_vs_previous = last_score - previous_score
    metrics = defin_feedback_classification(attention_scores)
    trend = analyze_attention_trend(attention_scores)

    return {
        "last_vs_previous": last_vs_previous,
        "trend": trend,
        "metrics": metrics,
        "error": None,
    }

def calculate_trend_slope(scores, times):
    if len(scores) != len(times) or len(scores) < 2:
        return 0 
    try:
        slope, _ = np.polyfit(times, scores, 1)     
        print(f"Calculated Trend Slope: {slope}")
        return slope
    except Exception as e:
        print(f"Error calculating trend slope: {e}")
        return 0



def generate_feedback(
    metrics, trend, last_vs_previous, score_threshold=10, std_threshold=10, trend_threshold=-30
):
    feedback = ""

    if metrics["std_dev"] > std_threshold:
        feedback += f"学生の集中度の変動が大きいです（標準偏差: {metrics['std_dev']:.2f}）。インタラクションを増やすか、授業の進め方を調整することを推奨します。\n"

    if metrics["mean"] < 60:
        feedback += "過去5分間の学生の集中度が低下しています。インタラクションを増やすか、授業の進め方を調整することを推奨します。\n"

    if metrics["trend_slope"] < 0 and trend == "Attention is decreasing":
        feedback += "集中度が低下傾向にあります（低下率: {:.2f}）。新しい授業要素を取り入れるか、短い休憩を挟むことを推奨します。\n".format(metrics["trend_slope"])
    elif metrics["trend_slope"] > 0 and trend == "Attention is increasing":
        feedback += "集中度が上昇傾向にあります。より難易度の高い内容を導入することを検討してください。\n"
    
    if abs(last_vs_previous) > score_threshold:
        if metrics["trend_slope"] > 0: 
            feedback += f"集中度が前より {last_vs_previous:.2f} 点上昇しました。\n"
        elif metrics["trend_slope"] < 0: 
            feedback += f"集中度が前より {abs(last_vs_previous):.2f} 点低下しました。\n"

    if not feedback:
        feedback = "学生の集中度は安定しています。この調子で続けてください。"

    return feedback



if __name__ == "__main__":
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    sql_file = "attention_data.sql"
    test_database_connection()
    app.run(debug=True)
