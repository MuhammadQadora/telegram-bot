pipeline {
  environment {
    c = credentials('dockerlogin')
  }
  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '5'))
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
        [key: 'ref', value: '$.ref'],
        [key: 'pusher', value: '$.pusher.name'],
        [key: 'modifiedFile', value: '$.commits[0].modified[0]']
      ],
      causeString: 'Triggered on $ref',
      token: '',
      tokenCredentialId: 'webhook-token',

      printContributedVariables: true,
      printPostContent: true,

      silentResponse: false,

      shouldNotFlatten: false,

      regexpFilterText: '$ref $modifiedFile',
      regexpFilterExpression: 'refs/heads/main Or.*'
    )
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
    stage('unit test'){
      steps{
        echo "some tests ran and passed ...."
      }
    }
    stage('scan with sonarqube'){
      steps{
        withSonarQubeEnv(credentialsId: 'sonar',installationName: 'sonar') {
          container('sonar'){
            echo "=====================================${STAGE_NAME}====================================="
            sh 'sonar-scanner -Dsonar.projectKey=myproject -Dsonar.sources=./Original-bot'
          }
        }
      }
    }
    stage('pip install'){
      steps{
        container('python'){
          sh 'pip install -r Original-bot/requirements.txt'
        }
      }
    }
    stage('snyk test'){
      steps{
        withCredentials([string(credentialsId: 'snykToken', variable: 'SNYK_TOKEN')]) {
        script {
          sh '''
          #!/bin/bash
          snyk test --package-manager=pip --json --severity-threshold=critical
          '''
          }
        }
      }
    }
  }
  post {
    always {
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
