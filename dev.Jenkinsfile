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
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    imagePullPolicy: Always
    command:
    - sleep
    args:
    - 9999999
    volumeMounts:
      - name: jenkins-docker-cfg
        mountPath: /kaniko/.docker
  volumes:
  - name: jenkins-docker-cfg
    projected:
      sources:
      - secret:
          name: docker-credentials 
          items:
            - key: .dockerconfigjson
              path: config.json
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
            sh 'sonar-scanner -Dsonar.projectKey=myproject -Dsonar.sources=./Original-bot 2> sonarResults.txt'
          }
        }
      }
    }
    stage('pip install'){
      steps{
        withCredentials([string(credentialsId: 'snykToken', variable: 'SNYK_TOKEN')]){
        container('python'){
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
    stage('Build Docker Image and push to ECR'){
      steps{
         container(name: 'kaniko', shell: '/busybox/sh'){
          echo "=====================================${STAGE_NAME}====================================="
          sh '''#!/busybox/sh
            cd Original-bot
            /kaniko/executor --context `pwd` --destination 933060838752.dkr.ecr.us-east-1.amazonaws.com/original-bot-dev:$BUILD_NUMBER
            /kaniko/executor --context `pwd` --destination 933060838752.dkr.ecr.us-east-1.amazonaws.com/original-bot-dev:latest 
          '''
         } 
      }
    }
  }
  post {
    failure {
      publishChecks actions: [[description: 'The build failed', identifier: '', label: 'bot-build-dev-status']], conclusion: 'FAILURE', name: 'devBuildCheck', title: 'devBuildCheck'
    }
    success {
      publishChecks actions: [[description: 'The build was successful ', identifier: '', label: 'buildstatus']], name: 'dev-bot-build-status', title: 'dev-bot-build-status'
    }
    always {
      echo "Archiving artifacts..."
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
