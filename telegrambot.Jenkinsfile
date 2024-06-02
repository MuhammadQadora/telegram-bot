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
    docker {
      label 'linux'
      image 'muhammadqadora/jenkins-inbound-agent:latest'
      args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
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
          checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/MuhammadQadora/telegram-bot']])
          echo 'Checked out from GitHub...'
        }
      }
    }
    stage('Docker Login') {
      steps {
        script {
          println("=====================================${STAGE_NAME}=====================================")
          sh """
            #!/bin/bash
            echo ${env.c_PSW} | docker login --username ${c_USR} --password-stdin
            echo "Success!"
          """
        }
      }
    }
    stage('Install requirements') {
      steps {
        script {
          println("=====================================${STAGE_NAME}=====================================")
          sh """
            #!/bin/bash
            apt install python3.11-venv -y
            python3 -m venv app
            . ./app/bin/activate
            pip install --no-cache-dir -r Original-bot/requirements.txt
            deactivate
            echo Success!
          """
        }
      }
    }
    stage('Docker Build')  {
      steps {
        script {
          println("=====================================${STAGE_NAME}=====================================")
          sh """
            #!/bin/bash
            docker build Original-bot \
            -t muhammadqadora/telegrambot-aws-terraform:${env.BUILD_NUMBER} -t muhammadqadora/telegrambot-aws-terraform:latest -f Original-bot/Dockerfile 
            docker push muhammadqadora/telegrambot-aws-terraform:latest
            docker push muhammadqadora/telegrambot-aws-terraform:${env.BUILD_NUMBER}
          """
        }
      }
    }
    stage('Trigger Deployment Pipeline') {
      steps {
        println("=====================================${STAGE_NAME}=====================================")
        build wait: false, job: 'telegram-bot-deployment'
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
