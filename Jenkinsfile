pipeline {
    agent any

    environment {
        APP_NAME = "aceest-app"
        DOCKER_IMAGE = "naveen1312/aceest-app"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        SONARQUBE_SERVER = "http://sonarqube:9000"
        KUBE_NAMESPACE = "default"
    }

    options {
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -eux
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    set -eux
                    . .venv/bin/activate
                    python -m compileall -q .
                    flake8 aceest_app tests app.py
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    set -eux
                    . .venv/bin/activate
                    PYTHONPATH=. pytest -q --cov=aceest_app --cov-report=xml --junitxml=pytest-report.xml
                '''
            }
            post {
                always {
                    junit 'pytest-report.xml'
                    archiveArtifacts artifacts: 'coverage.xml', onlyIfSuccessful: false
                }
            }
        }

        stage('SonarQube Scan') {
            steps {
                withSonarQubeEnv("${SONARQUBE_SERVER}") {
                    sh '''
                        set -eux
                        . .venv/bin/activate
                        sonar-scanner
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -eux
                    docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} -t ${DOCKER_IMAGE}:latest .
                '''
            }
        }

        stage('Push Docker Image') {
            when {
                anyOf {
                    branch 'main'
                    branch 'dev'
                }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USER',
                    passwordVariable: 'DOCKERHUB_PASS'
                )]) {
                    sh '''
                        set -eux
                        echo "$DOCKERHUB_PASS" | docker login -u "$DOCKERHUB_USER" --password-stdin
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        stage('Deploy To Kubernetes') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-credentials', variable: 'KUBECONFIG_FILE')]) {
                    sh '''
                        set -eux
                        export KUBECONFIG="$KUBECONFIG_FILE"
                        sed "s|IMAGE_TAG|${IMAGE_TAG}|g" k8s/deployment.yaml | kubectl apply -n ${KUBE_NAMESPACE} -f -
                        kubectl apply -n ${KUBE_NAMESPACE} -f k8s/service.yaml
                        kubectl rollout status deployment/aceest-app-deployment -n ${KUBE_NAMESPACE} --timeout=180s
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully. Docker image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline failed. Check the failed stage logs and SonarQube quality gate.'
        }
        always {
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
    }
}
