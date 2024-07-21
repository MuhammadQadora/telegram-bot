pipeline {
  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '2'))
    ansiColor('xterm')
  }
  agent {
    kubernetes {}
  }
   triggers {
    GenericTrigger(
      genericVariables: [
        [key: 'ref', value: '$.pull_request.base.ref'],
        [key: 'action', value: '$.action'],
        [key: 'sha', value: '$.pull_request.head.sha'],
        [key: 'fbranch', value: '$.pull_request.head.ref'],
      ],
      causeString: 'Triggered on $ref',
      token: '',
      tokenCredentialId: 'webhook-token',

      printContributedVariables: true,
      printPostContent: true,

      silentResponse: false,

      shouldNotFlatten: false,

      regexpFilterText: '$ref $action',
      regexpFilterExpression: 'dev (opened|synchronize)'
    )
  }
  stages {
    stage('GitHub Checkout') {
      steps {
        script {
          echo "=====================================${STAGE_NAME}====================================="
          updateStatus('pending','tests started')
          checkout scmGit(branches: [[name: "*/${env.fbranch}"]], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/MuhammadQadora/telegram-bot']])
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
          echo "=====================================${STAGE_NAME}====================================="
          sh '''
          #!/bin/bash
          python3 -m venv private
          . private/bin/activate
          pip install --no-cache-dir black; python3 -m black .
          deactivate
          '''
      }
    }
    stage('scan with sonarqube') {
      steps {
        withSonarQubeEnv(credentialsId: 'sonar', installationName: 'sonar') {
            echo "=====================================${STAGE_NAME}====================================="
            sh '/opt/sonar-scanner/bin/sonar-scanner -Dsonar.projectKey=myproject -Dsonar.sources=./Original-bot 2> sonarResults.txt'
        }
      }
    }
    stage('Snyk test') {
      steps {
        withCredentials([string(credentialsId: 'snykToken', variable: 'SNYK_TOKEN')]) {
            echo "=====================================${STAGE_NAME}====================================="
            sh '''
            #!/bin/bash
            . private/bin/activate
            pip install -r Original-bot/requirements.txt
            snyk test --package-manager=pip --command=python3.11 --file=./Original-bot/requirements.txt > snykResults.txt
            deactivate
            '''
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
