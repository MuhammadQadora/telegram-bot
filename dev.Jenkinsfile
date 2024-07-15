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
      regexpFilterExpression: 'refs/heads/dev Or.*'
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
    stage('update tag version'){
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'token', usernameVariable: 'user')]){
        script {
          env.v = sh(returnStdout: true, script: '''
          #!/bin/bash
          vnum=$(( $(cat dev-version.txt | tr -d '.') + 1 ))
          v=$(echo $vnum | sed 's/./&./g' | sed 's/.$//g' )
          echo $v | tee dev-version.txt
          ''').trim()
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
            /kaniko/executor --context `pwd` --destination 933060838752.dkr.ecr.us-east-1.amazonaws.com/original-bot-dev:$v
            /kaniko/executor --context `pwd` --destination 933060838752.dkr.ecr.us-east-1.amazonaws.com/original-bot-dev:latest
          '''
         } 
      }
    }
    stage('push to github'){
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'token', usernameVariable: 'user')]){
        script {
           sh '''
          git config --global user.name "$user"
          git config --global user.email "memomq70@gmail.com"
          git remote set-url origin https://$user:$token@github.com/MuhammadQadora/telegram-bot
          export check=$(git status | grep clean)
          if [ "$check" = "nothing to commit, working tree clean" ];then echo yes && exit 0;fi
          git checkout dev
          git add .
          git commit -m "Commit by Jenkins: updated tag to $version"
          git push origin dev
          '''
          }
        }
      }
    }
    stage('clean workspace'){
      steps{
        echo "=====================================${STAGE_NAME}====================================="
        cleanWs()
      }
    }
    stage('checkout from GitOps'){
      steps{
        echo "=====================================${STAGE_NAME}====================================="
        checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/MuhammadQadora/GitOps']])
      }
    }
    stage('update chart and app verison'){
      steps {
        script {
          sh '''
          #!/bin/bash
          sed -i "s/tag: .*/tag: $v/" ./environments/dev/bot-chart/values.yaml
          sed -i "s/appVersion: .*/appVersion: $v/" ./environments/dev/bot-chart/Chart.yaml
          '''
        }
      }
    }
    stage('trigger git push pipeline'){
        steps{
            withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'token', usernameVariable: 'user')]) {
                script {
                    sh '''
                    #!/bin/bash
                    git config --global user.name "$user"
                    git config --global user.email "memomq70@gmail.com"
                    git remote set-url origin https://$user:$token@github.com/MuhammadQadora/GitOps
                    export check=$(git status | grep clean)
                    if [ "$check" = "nothing to commit, working tree clean" ];then echo yes && exit 0;fi
                    git checkout main
                    git add .
                    git commit -m "Commit by Jenkins: updated tag to $v"
                    git push origin main
                    '''
                }
            }
        }
    }
  }
  post {
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
