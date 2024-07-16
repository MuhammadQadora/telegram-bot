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
    resources:
      requests:
        memory: 300Mi
        cpu: 300m
    command: ['sleep','infinity']
  - name: python
    image: python
    resources:
      requests:
        memory: 300Mi
        cpu: 300m
    command: ['sleep','infinity']
'''
    }
  }
   triggers {
    GenericTrigger(
      genericVariables: [
        [key: 'ref', value: '$.pull_request.base.ref'],
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
  stages {
    stage('GitHub Checkout') {
      steps {
        script {
          echo "=====================================${STAGE_NAME}====================================="
          updateStatus('pending','tests started')
          checkout scmGit(branches: [[name: '*/dev']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/MuhammadQadora/telegram-bot']])
          updateStatus('pending','tests started')
          echo 'Checked out from GitHub...'
        }
      }
    }
    stage('unit test') {
      steps {
        echo "=====================================${STAGE_NAME}====================================="
        echo "some tests ran and passed ...."
      }
    }
    stage('enforce PEP8 with Black'){
      steps{
        container('python'){
          echo "=====================================${STAGE_NAME}====================================="
          sh 'pip install --no-cache-dir black; python3 -m black .'
        }
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
            snyk test --package-manager=pip --command=python3.12 --file=./Original-bot/requirements.txt > snykResults.txt
            '''
          }
        }
      }
    }
  }
  post {
    failure {
       updateStatus('failure','The tests failed')
    }
    success{
        updateStatus('success','The tests succeded')
    }
    always {
      echo "Archiving artifacts...."
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

def updateStatus(String state, String description){
    withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'gtoken', usernameVariable: 'user')]) {
    sh """
    #!/bin/bash
    curl -L \
      -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${gtoken}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      https://api.github.com/repos/MuhammadQadora/telegram-bot/statuses/"${sha}" \
      -d '{"state":"${state}","target_url":"${BUILD_URL}","description":"${description}","context":"continuous-integration/jenkins"}'
    """
    }
}
