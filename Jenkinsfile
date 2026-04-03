pipeline {
  agent any

  stages {
    stage('Checkout') {
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
          python -m pytest -q --cov=aceest_app
        '''
      }
    }
  }
}

