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