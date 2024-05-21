pipeline {
  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '5'))
    ansiColor('xterm')
  }
  parameters {
    string(name: 'region', defaultValue: 'ap-northeast-1', description: 'The region to deploy to')
  }
  agent {
    docker {
      label 'linux'
      image 'muhammadqadora/jenkins-inbound-agent'
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
      token: '1111',
      tokenCredentialId: '',

      printContributedVariables: true,
      printPostContent: true,

      silentResponse: false,

      shouldNotFlatten: false,

      regexpFilterText: '$ref $modifiedFile',
      regexpFilterExpression: 'refs/heads/main ^Original.*'
    )
  }
  environment {
    TF_VAR_ec2_public_key = credentials('ec2-public-key')
  }
  stages {
    stage('Print Params') {
      when {
        expression { env.ref != null } // Run only if triggered by webhook
      }
      steps {
        script {
          echo "${env.ref}"
          echo "=====================================${STAGE_NAME}====================================="
          echo "=====================================${BUILD_NUMBER}====================================="
          echo "=====================================${env.pusher}====================================="
          echo "=====================================${params.region}====================================="
        }
      }
    }
    stage('GitHub Checkout') {
      steps {
        script {
          echo "=====================================${STAGE_NAME}====================================="
          checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/MuhammadQadora/terraform-bot-mf']])
          echo 'Checked out from GitHub...'
        }
      }
    }
  }
  post {
    always {
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
