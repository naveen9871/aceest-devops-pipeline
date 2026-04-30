pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "naveen9871/aceest-app"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        SONARQUBE_SERVER = "sonarqube"
        KUBECONFIG_PATH = "/var/jenkins_home/kubeconfig"
        // DOCKER_CRED = credentials('dockerhub-credentials')
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Clean Build & Quality Gate') {
            steps {
                sh '''
                    set -e
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m compileall -q .
                    flake8 aceest_app tests app.py
                    PYTHONPATH=. python -m pytest -q --cov=aceest_app --junitxml=pytest-report.xml
                '''
            }
/*
            post {
                always {
                    junit 'pytest-report.xml'
                }
            }
*/
        }

/*
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv(SONARQUBE_SERVER) {
                    sh 'sonar-scanner -Dsonar.projectKey=aceest-app -Dsonar.sources=.'
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
*/

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
            }
        }

/*
        stage('Push to Docker Hub') {
            steps {
                sh "echo \$DOCKER_CRED_PSW | docker login -u \$DOCKER_CRED_USR --password-stdin"
                sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker push ${DOCKER_IMAGE}:latest"
            }
        }
*/

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                export KUBECONFIG=$KUBECONFIG_PATH
                sed -i "s/IMAGE_TAG/${DOCKER_TAG}/g" k8s/deployment.yaml
                kubectl apply -f k8s/deployment.yaml
                kubectl apply -f k8s/service.yaml
                '''
            }
        }
    }
}
