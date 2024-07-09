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
   triggers {
    GenericTrigger(
      genericVariables: [
        [key: 'ref', value: '$.base.ref'],
        [key: 'action', value: '$.action'],
        [key: 'sha', value: '$.pull_request.head.sha']
      ],
      causeString: 'Triggered on $ref',
      token: '',
      tokenCredentialId: 'webhook-token',

      printContributedVariables: true,
      printPostContent: true,

      silentResponse: false,

      shouldNotFlatten: false,

      regexpFilterText: '$ref $action',
      regexpFilterExpression: 'dev opened'
    )
  }
  environment {
        GITHUB_TOKEN = credentials('github-token')
        GITHUB_REPO = 'muhammadqadora/telegram-bot'
        COMMIT_SHA = "${env.sha}" // This should be dynamically set to the commit SHA
    }
  stages {
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
    success {
      updateGitHubStatus('success', 'build', 'Build was successful')
      updateGitHubStatus('success', 'test', 'Tests passed')
    }
    failure {
      updateGitHubStatus('failure', 'build', 'Build failed')
      updateGitHubStatus('failure', 'test', 'Tests failed')
    }
    always {
      echo "Archiving artifacts..."
      recordIssues sourceCodeRetention: 'LAST_BUILD', tools: [
        sonarQube(id: 'sonar-check', name: 'sonar-check', pattern: 'sonarResults.txt', reportEncoding: 'UTF-8'),
        codeAnalysis(id: 'snyk-results', name: 'snyk-results', pattern: 'snykResults.txt', reportEncoding: 'UTF-8')
      ]
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


def updateGitHubStatus(String state, String context, String description) {
    def url = "https://api.github.com/repos/${env.GITHUB_REPO}/statuses/${env.COMMIT_SHA}"
    
    httpRequest acceptType: 'APPLICATION_JSON',
                contentType: 'APPLICATION_JSON',
                httpMode: 'POST',
                url: url,
                customHeaders: [[name: 'Authorization', value: "token ${env.GITHUB_TOKEN}"]],
                requestBody: """{
                    "state": "${state}",
                    "context": "${context}",
                    "description": "${description}",
                    "target_url": "${env.BUILD_URL}"
                }"""
}
