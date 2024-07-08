pipeline {
  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '2'))
    ansiColor('xterm')
  }
  agent {
    kubernetes {
      yaml '''
apiVersion: v1
kind: Pod
metadata:
  name: sonar
spec:
  containers:
  - name: sonar
    image: sonarsource/sonar-scanner-cli
    command: ['sleep','infinity']
  - name: python
    image: python
    command: ['sleep','infinity']
'''
    }
  }
  stages {
    stage('Print Params') {
      when {
        expression { env.ref != null } // Run only if triggered by webhook
      }
      steps {
        script {
          echo "=====================================${STAGE_NAME}====================================="
          echo "Build Number: ${BUILD_NUMBER}"
          echo "Pusher: ${env.pusher}"
          echo "Region: ${params.region}"
        }
      }
    }
    stage('GitHub Checkout') {
      steps {
        script {
          echo "=====================================${STAGE_NAME}====================================="
          checkout scmGit(branches: [[name: '*/dev']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/MuhammadQadora/telegram-bot']])
          echo 'Checked out from GitHub...'
        }
      }
    }
    stage('unit test') {
      steps {
        echo "some tests ran and passed ...."
      }
    }
    stage('scan with sonarqube') {
      steps {
        withSonarQubeEnv(credentialsId: 'sonar', installationName: 'sonar') {
          container('sonar') {
            echo "=====================================${STAGE_NAME}====================================="
            sh 'sonar-scanner -Dsonar.projectKey=myproject -Dsonar.sources=./Original-bot 2> sonarResults.txt'
          }
        }
      }
    }
    stage('Snyk test') {
      steps {
        withCredentials([string(credentialsId: 'snykToken', variable: 'SNYK_TOKEN')]) {
          container('python') {
            echo "=====================================${STAGE_NAME}====================================="
            sh '''
            #!/bin/bash
            apt update && curl https://static.snyk.io/cli/latest/snyk-linux?_gl=1*1d1iprh*_gcl_au*MTUxOTIyNjI1Ny4xNzIwMDczMTE3*_ga*MTE0MTA4NjM3MS4xNzIwMDczMTE3*_ga_X9SH3KP7B4*MTcyMDExODU1My41LjEuMTcyMDExODU1Ni41Ny4wLjA. -o snyk
            chmod +x ./snyk
            mv ./snyk /usr/local/bin/
            pip install -r Original-bot/requirements.txt
            snyk test --package-manager=pip --command=python3.12 --file=./Original-bot/requirements.txt 2> snykResults.txt
            '''
          }
        }
      }
    }
  }
  post {
    always {
      echo "Archiving artifacts..."
      recordIssues sourceCodeRetention: 'LAST_BUILD', tools: [
        sonarQube(id: 'sonar-check', name: 'sonar-check', pattern: 'sonarResults.txt', reportEncoding: 'UTF-8'),
        codeAnalysis(id: 'snyk-results', name: 'snyk-results', pattern: 'snykResults.txt', reportEncoding: 'UTF-8')
      ]
      githubPRStatusPublisher(
        buildMessage: message(
          failureMsg: githubPRMessage('Can\'t set status; build failed.'),
          successMsg: githubPRMessage('Build succeeded.')
        ),
        statusMsg: githubPRMessage('Build ended.'),
        statusVerifier: allowRunOnStatus('SUCCESS'),
        unstableAs: 'FAILURE',
        errorHandler: statusOnPublisherError('FAILURE')
      )
      archiveArtifacts allowEmptyArchive: true, artifacts: '*.txt', followSymlinks: false, onlyIfSuccessful: true
      cleanWs()
      emailext(
        attachLog: true,
        body: '''$PROJECT_NAME - Build # $BUILD_NUMBER - $BUILD_STATUS:
              Check console output at $BUILD_URL to view the results.''',
        subject: '$PROJECT_NAME - Build # $BUILD_NUMBER - $BUILD_STATUS!',
        to: 'memomq70@gmail.com, firas.narani.1999@outlook.com'
      )
    }
  }
}
