
xdyu@xdyu-Alienware:~$ cd /home/xdyu/Projects/Job-fit-engine
./tests/verify_api_for_screenshots.sh
==============================================
截图 1: 后端健康检查
==============================================

$ curl http://localhost:8000/health

{
    "status": "ok",
    "message": "Tech Career Fit Engine is running"
}

==============================================
截图 2: 上传简历
==============================================

$ curl -X POST http://localhost:8000/resume/upload/json -H 'Content-Type: application/json' -d '{"text": "..."}'

{
    "session_id": "f84996c7",
    "upload_id": "5e4a6324e8cd"
}

等待简历处理完成...
.....状态: ready

==============================================
截图 3: AI 功能验证 - POST /analyze/fit
==============================================

$ curl -X POST http://localhost:8000/analyze/fit -H 'Content-Type: application/json' -d '{...}'

{
    "recommended_roles": [
        {
            "role": "MLE",
            "score": 0.6,
            "reasons": [
                "The candidate has experience designing and deploying ML models.",
                "The candidate has built end-to-end ML pipelines.",
                "The candidate has built backend services supporting ML inference APIs.",
                "The candidate has an M.S. in Computer Science."
            ]
        }
    ],
    "requirements": {
        "must_have": [
            "Python",
            "PyTorch",
            "model deployment",
            "MLOps",
            "5+ years"
        ],
        "nice_to_have": []
    },
    "gap": {
        "matched": [
            "model deployment",
            "MLOps"
        ],
        "missing": [
            "Python",
            "PyTorch",
            "5+ years"
        ],
        "ask_user_questions": [
            "Does the candidate have experience with Python and PyTorch?",
            "How many years of relevant experience does the candidate have?"
        ]
    },
    "evidence": {
        "resume_chunks": [
            {
                "chunk_id": "exp_f1294f9d__experience__0",
                "text": "EXPERIENCE\n- Designed and deployed ML models for ranking and personalization serving 10M+ users.\n- Built end-to-end ML pipelines including feature generation, training, and inference.\n- Implemented model monitoring, drift detection, and retraining workflows.\n- Partnered with product and data science teams to translate research into production.",
                "source": "resume",
                "score": 0.6478614807128906
            },
            {
                "chunk_id": "exp_12c5c898__experience__0",
                "text": "EXPERIENCE\n- Developed predictive models for churn and engagement.\n- Conducted A/B tests and statistical analyses to validate model impact.",
                "source": "resume",
                "score": 0.6196883916854858
            },
            {
                "chunk_id": "exp_be81a06b__experience__0",
                "text": "EXPERIENCE\n- Built backend services supporting ML inference APIs.\n- Improved system latency and reliability for data-intensive services.",
                "source": "resume",
                "score": 0.6103913187980652
            },
            {
                "chunk_id": "edu_56ed7888__education__0",
                "text": "M.S. Computer Science",
                "source": "resume",
                "score": 0.5129895210266113
            }
        ],
        "jd_chunks": [
            {
                "chunk_id": "temp_jd_0",
                "text": "ML Engineer: Python, PyTorch, model deployment, MLOps, 5+ years.",
                "source": "jd",
                "score": 0.663343071937561
            }
        ]
    }
}

==============================================
截图 4: AI 功能验证 - POST /resume/generate
==============================================

$ curl -X POST http://localhost:8000/resume/generate -H 'Content-Type: application/json' -d '{...}'

{
    "resume_markdown": "## Education\n- M.S. Computer Science\n\n## Experience\n- Designed and deployed ML models for ranking and personalization serving 10M+ users.\n- Built end-to-end ML pipelines including feature generation, training, and inference.\n- Implemented model monitoring, drift detection, and retraining workflows.\n- Partnered with product and data science teams to translate research into production.\n- Built backend services supporting ML inference APIs.\n- Improved system latency and reliability for data-intensive services.\n- Developed predictive models for churn and engagement.\n- Conducted A/B tests and statistical analyses to validate model impact.\n\n## Skills\n_No skills information available._",
    "resume_structured": {
        "education": [
            "M.S. Computer Science"
        ],
        "experience": [
            "Designed and deployed ML models for ranking and personalization serving 10M+ users.",
            "Built end-to-end ML pipelines including feature generation, training, and inference.",
            "Implemented model monitoring, drift detection, and retraining workflows.",
            "Partnered with product and data science teams to translate research into production.",
            "Built backend services supporting ML inference APIs.",
            "Improved system latency and reliability for data-intensive services.",
            "Developed predictive models for churn and engagement.",
            "Conducted A/B tests and statistical analyses to validate model impact."
        ],
        "skills": []
    },
    "need_info": [
        "Python",
        "PyTorch",
        "model deployment"
    ],
    "evidence": {
        "resume_chunks": [
            {
                "chunk_id": "exp_f1294f9d__experience__0",
                "text": "EXPERIENCE\n- Designed and deployed ML models for ranking and personalization serving 10M+ users.\n- Built end-to-end ML pipelines including feature generation, training, and inference.\n- Implemented model monitoring, drift detection, and retraining workflows.\n- Partnered with product and data science teams to translate research into production.",
                "source": "resume",
                "score": 0.6207737922668457
            },
            {
                "chunk_id": "exp_be81a06b__experience__0",
                "text": "EXPERIENCE\n- Built backend services supporting ML inference APIs.\n- Improved system latency and reliability for data-intensive services.",
                "source": "resume",
                "score": 0.5971680879592896
            },
            {
                "chunk_id": "exp_12c5c898__experience__0",
                "text": "EXPERIENCE\n- Developed predictive models for churn and engagement.\n- Conducted A/B tests and statistical analyses to validate model impact.",
                "source": "resume",
                "score": 0.5915939807891846
            },
            {
                "chunk_id": "edu_56ed7888__education__0",
                "text": "M.S. Computer Science",
                "source": "resume",
                "score": 0.5384840369224548
            }
        ],
        "jd_chunks": [
            {
                "chunk_id": "temp_jd_0",
                "text": "ML Engineer: Python, PyTorch, model deployment.",
                "source": "jd",
                "score": 0.6346420049667358
            }
        ]
    }
}

验证完成。请对上述输出截图。

