//data_upload.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.getElementById('upload-button');
    const analysisButton = document.getElementById('analysis-button');
    const statusMessage = document.getElementById('statusMessage');
    const resultMessage = document.getElementById('resultMessage');

    if (!sessionStorage.getItem('statusInitialized')) {
        statusMessage.textContent = 'Please upload a CSV file.';
        statusMessage.style.color = 'red';
        resultMessage.textContent = '';
        resultMessage.style.color = '';
        sessionStorage.setItem('statusInitialized', true);
    }

    if (uploadButton && analysisButton) {
        document.getElementById('upload-button').addEventListener('click', function () {
            event.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const formData = new FormData();
            if (!fileInput.files[0]) {
                document.getElementById('statusMessage').textContent = 'Please select a file before uploading.';
                document.getElementById('statusMessage').style.color = 'red';
                document.getElementById('resultMessage').textContent = '';
                document.getElementById('resultMessage').style.color = '';
                return;
            }

            formData.append('file', fileInput.files[0]);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('statusMessage').textContent = data.error;
                        document.getElementById('statusMessage').style.color = 'red';
                        document.getElementById('resultMessage').textContent = '';
                        document.getElementById('resultMessage').style.color = '';
                    } else {
                        document.getElementById('statusMessage').textContent = 'File uploaded successfully.';
                        document.getElementById('statusMessage').style.color = 'green';
                        document.getElementById('resultMessage').textContent = 'Please click on Analysis';
                        document.getElementById('resultMessage').style.color = 'red';
                        sessionStorage.setItem('filepath', data.filepath);
                        console.log('Filepath saved to sessionStorage', sessionStorage.getItem('filepath'));
                    }
                })
                .catch(error => {
                    console.error('Upload failed', error);
                    document.getElementById('statusMessage').textContent = 'An error occurred during upload.';
                    document.getElementById('statusMessage').style.color = 'red';
                    document.getElementById('resultMessage').textContent = '';
                    document.getElementById('resultMessage').style.color = '';
                });
        });



        document.getElementById('analysis-button').addEventListener('click', function () {
            const filepath = sessionStorage.getItem('filepath');
            if (!filepath) {
                console.error('No filepath found in session storage');
                document.getElementById('statusMessage').textContent = 'Please upload a CSV file before analyzing.';
                document.getElementById('statusMessage').style.color = 'red';
                document.getElementById('resultMessage').textContent = '';
                document.getElementById('resultMessage').style.color = '';
                return;
            }

            fetch('/analyze', {
                method: 'POST',
                body: JSON.stringify({ filepath: filepath }),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    } return response.json();
                })
                .then(data => {
                    console.log(data);
                    if (data.error) {
                        document.getElementById('statusMessage').textContent = data.error;
                        document.getElementById('statusMessage').style.color = 'red';
                        document.getElementById('resultMessage').textContent = '';
                        document.getElementById('resultMessage').style.color = '';
                    } else {
                        document.getElementById('statusMessage').textContent = 'Analysis successful. Redirecting...';
                        document.getElementById('statusMessage').style.color = 'green';
                        document.getElementById('resultMessage').textContent = '';
                        document.getElementById('resultMessage').style.color = '';

                        setTimeout(() => {
                            window.location.href = '/login-selection';
                        }, 1000);
                    }
                })
                .catch(error => {
                    console.error('Error during analysis', error);
                    document.getElementById('statusMessage').textContent = 'An error occurred during analysis.';
                    document.getElementById('statusMessage').style.color = 'red';
                });
        });

    }
});


//login_selection.js
document.addEventListener('DOMContentLoaded', () => {
    const teacherLoginButton = document.getElementById('teacher-login-button');
    const studentLoginButton = document.getElementById('student-login-button');
    const ReuploadButton = document.getElementById('Reupload');
    if (teacherLoginButton && studentLoginButton) {
        teacherLoginButton.addEventListener('click', () => {
            console.log('Redirecting to /teacher-login');
            window.location.href = '/teacher-login';
        });

        studentLoginButton.addEventListener('click', () => {
            console.log('Redirecting to /student-login');
            window.location.href = '/student-login';
        });

        ReuploadButton.addEventListener('click', () => {
            console.log('Redirecting to /');
            window.location.href = '/';
        });
    }
});


//teacher_login.js
document.addEventListener('DOMContentLoaded', () => {
    const teacherLoginForm = document.getElementById('teacher-loginForm')
    if (teacherLoginForm) {
        teacherLoginForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const teacherUsername = document.getElementById('teacher-username').value;
            const teacherPassword = document.getElementById('teacher-password').value;
            const errorMessage = document.getElementById('error-message');
            try {
                const response = await fetch('/teacher-login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ "teacher-username": teacherUsername, "teacher-password": teacherPassword })
                });
                if (!response.ok) {
                    throw new Error("Invalid username or password");
                }
                const result = await response.json();
                if (result.error) {
                    errorMessage.textContent = result.error;
                    errorMessage.style.display = "block";
                    errorMessage.style.color = 'red';
                } else {
                    errorMessage.textContent = 'Loading...';
                    errorMessage.style.color = 'green';
                    errorMessage.style.display = "block";

                    setTimeout(() => {
                        window.location.href = '/teacher-dashboard';
                    }, 1000);
                }
            } catch (error) {
                console.error('Error:', error);
                errorMessage.textContent = "Please enter the correct username or password."
                errorMessage.style.display = "block";
            }
        });

        const TeacherLoginBackToLoginSelection = document.getElementById('teacher_login-back-to-login_selection');
        if (TeacherLoginBackToLoginSelection) {
            TeacherLoginBackToLoginSelection.addEventListener('click', () => {
                console.log('Redirecting to /login-selection');
                window.location.href = '/login-selection';
            });
        }
    }
});

//student_login.js
document.addEventListener('DOMContentLoaded', () => {
    const studentLoginForm = document.getElementById('student-loginForm')
    if (studentLoginForm) {
        studentLoginForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const studentUsername = document.getElementById('student-username').value;
            const studentPassword = document.getElementById('student-password').value;
            const errorMessage = document.getElementById('error-message');
            try {
                const response = await fetch('/student-login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ "student-username": studentUsername, "student-password": studentPassword })
                });
                if (!response.ok) {
                    throw new Error("Invalid username or password");
                }
                const result = await response.json();
                if (result.error) {
                    errorMessage.textContent = result.error;
                    errorMessage.style.display = "block";
                    errorMessage.style.color = 'red';
                } else if (result.success) {
                    errorMessage.textContent = 'Login successful,Loading...';
                    errorMessage.style.color = 'green';
                    errorMessage.style.display = "block";
                    setTimeout(() => {
                        window.location.href = `/student-dashboard?class_id=${result.class_id}&student_id=${result.student_id}`;
                    }, 1000);
                } else {
                    throw new Error("Failed to load student plot");
                }
            } catch (error) {
                console.error('Error:', error);
                errorMessage.textContent = "Please enter the correct username or password."
                errorMessage.style.display = "block";
                errorMessage.style.color = 'red';
            }
        });

        const StudentLoginBackToLoginSelection = document.getElementById('student_login-back-to-login_selection');
        if (StudentLoginBackToLoginSelection) {
            StudentLoginBackToLoginSelection.addEventListener('click', () => {
                console.log('Redirecting to /login-selection');
                window.location.href = '/login-selection';
            });
        }
    }
});


async function getFeedback(student_id, class_id, chatCard) {
    try {
        console.log(`Fetching feedback for student ${student_id}, class ${class_id}`);
        const response = await fetch(`/get-data?student_id=${student_id}&class_id=${class_id}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const result = await response.json();
        console.log("Feedback data:", result);

        if (result.error) {
            throw new Error(result.error);
        }

        const feedbackOverlay = chatCard.querySelector('.feedback-overlay');
        if (result.feedback) {
            feedbackOverlay.textContent = result.feedback;
            feedbackOverlay.style.color = '#333';
        } else {
            feedbackOverlay.textContent = 'No feedback available.';
            feedbackOverlay.style.color = '#999';
        }
    } catch (error) {
        console.error(`Error fetching feedback: ${error}`);
        const feedbackOverlay = chatCard.querySelector('.feedback-overlay');
        feedbackOverlay.textContent = 'Failed to load feedback.';
        feedbackOverlay.style.color = 'red';
    }
}

//teacher_dashboard.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("Script loaded, attempting to fetch plots...");
    const plotContainer = document.getElementById('chartsContainer');
    const imageModal = document.getElementById('imageModal');
    const modalContent = document.getElementById("modalContent");
    const span = document.getElementsByClassName("close")[0];
    console.log("plotContainer:", plotContainer);

    if (!plotContainer) {
        console.error("chartsContainer not found in the DOM!");
        return;
    } console.log("chartsContainer successfully found!");

    if (plotContainer) {
        fetch('/get-plots?user_type=teacher')
            .then(response => response.json())
            .then(data => {
                console.log("Received data:", data);

                if (data.plots && data.plots.length > 0) {
                    data.plots.sort((a, b) => {
                        if (a.class_id !== b.class_id) {
                            return a.class_id - b.class_id;
                        }
                        return a.student_id - b.student_id;
                    });

                    data.plots.forEach(plot => {
                        console.log("processing plot:", plot);
                        const chatCard = document.createElement('div');
                        chatCard.className = 'card';
                        chatCard.innerHTML = `
                            <h3> class ${plot.class_id} - student ${plot.student_id}</h3>
                            <img src="${plot.plot_url}" alt="Attention Chart">
                            <div class="feedback-overlay">Loading feedback</div>
                            <div class ="escalate-icon"></div>
                        `;
                        plotContainer.appendChild(chatCard);

                        fetch(`/get-data?student_id=${plot.student_id}&class_id=${plot.class_id}`)
                            .then(response => response.json())
                            .then(result => {
                                const feedbackOverlay = chatCard.querySelector('.feedback-overlay');
                                if (result.feedback) {
                                    feedbackOverlay.textContent = result.feedback;
                                    feedbackOverlay.style.color = '#333';
                                } else {
                                    feedbackOverlay.textContent = 'No feedback available.';
                                    feedbackOverlay.style.color = '#999';
                                }
                            })
                            .catch(error => {
                                console.error("Error fetching feedback:", error);
                                const feedbackOverlay = chatCard.querySelector('.feedback-overlay');
                                feedbackOverlay.textContent = 'Failed to load feedback.';
                                feedbackOverlay.style.color = 'red';
                            });

                        //escalate img
                        const escalateIcon = chatCard.querySelector('.escalate-icon');
                        const img = chatCard.querySelector('img');
                        escalateIcon.addEventListener('click', () => {
                            imageModal.style.display = 'flex';
                            modalContent.src = img.src;

                            fetch(`/get-data?student_id=${plot.student_id}&class_id=${plot.class_id}`)
                                .then(response => response.json())
                                .then(result => {
                                    const feedback = document.getElementById('modalFeedback');
                                    if (result.feedback) {
                                        feedback.textContent = result.feedback;
                                    } else {
                                        feedback.textContent = 'No feedback available.';
                                        feedback.style.color = '#999';
                                    }
                                })
                                .catch(error => {
                                    console.error('Error fetching feedback for modal:', error);
                                    const feedback = document.getElementById('modalFeedback');
                                    feedback.textContent = 'Failed to load feedback.';
                                    feedback.style.color = 'red';
                                });
                        });
                    });
                } else {
                    plotContainer.textContent = 'No attention data available';
                }
            })
            .catch(error => {
                console.error('Error fetching plots:', error);
                plotContainer.textContent = 'Error loading plots. Please try again later.';
            });
    }

    span.onclick = function () {
        imageModal.style.display = "none";
    };

    window.onclick = function (event) {
        if (event.target == imageModal) {
            imageModal.style.display = "none";
        }
    };

    const TeacherLogout = document.getElementById('teacher-logout');
    if (TeacherLogout) {
        TeacherLogout.addEventListener('click', () => {
            console.log('Redirecting to /login-selection');
            window.location.href = '/login-selection';
        });
    }
});


//student_dashboard.js
document.addEventListener('DOMContentLoaded', () => {
    const studentPlot = localStorage.getItem('studentPlot');
    const studentPlotContainer = document.getElementById('student-plotContainer');

    if (!studentPlotContainer) {
        console.error("student-plotContainer not found in the DOM!");
        return;
    } console.log("student-plotContainer successfully found!");

    const urlParams = new URLSearchParams(window.location.search);
    const classId = urlParams.get('class_id');
    const studentId = urlParams.get('student_id');

    if (!classId || !studentId) {
        console.error('Missing class_id or student_id not found in the URL parameters');
        studentPlotContainer.textContent = 'Error: Missing class_id or student_id';
        return;
    }

    fetch(`/get-student-plots?class_id=${classId}&student_id=${studentId}`)
        .then(response => response.json())
        .then(data => {
            if (data.plot_url) {
                const studentPlotContainer = document.getElementById('student-plotContainer');
                const studentPlotImage = document.createElement('img');
                studentPlotImage.src = data.plot_url;
                studentPlotImage.alt = 'Student Attention Plot';
                studentPlotImage.className = 'student-card';
                studentPlotContainer.appendChild(studentPlotImage);

                const feedbackContainer = document.createElement('div');
                feedbackContainer.className = 'feedback-container';
                studentPlotContainer.appendChild(feedbackContainer);

                getFeedback(studentId, classId)
                    .then(feedback => {
                        const feedbackOverlay = chatCard.querySelector('.feedback-overlay');
                        feedbackOverlay.textContent = feedback;
                    });
            } else {
                studentPlotContainer.textContent = 'No plots available for this student';
            }
        })
        .catch(error => {
            console.error('Error fetching student plot:', error);
            studentPlotContainer.textContent = 'Failed to load data. Check database connection.';
        });


    const studentLogout = document.getElementById('student-logout');
    if (studentLogout) {
        console.log('Found student-logout button:', studentLogout);
        studentLogout.addEventListener('click', () => {
            console.log('Redirecting to /login-selection');
            location.assign('/login-selection');
            window.location.href = '/login-selection';
        });
    } else {
        console.error('student-logout button not found in DOM');
    }
});

//feedback submittal.js
setInterval(function () {
    let currentAttentionScore = getCurrentAttentionScore();
    fetch('/updata-attention', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            student_id: studentId,
            attention_score: currentAttentionScore
        })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('feedback').textContent = data.feedback;
        })
        .catch(error => {
            console.error('Error updating attention score:', error);
        });
}, 60000);
