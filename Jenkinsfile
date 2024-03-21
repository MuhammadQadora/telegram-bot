pipeline{
  agent any
  stages {
    stage('hello shell script'){
      environment {
        ABC = "chupapy"
        cp = "lord"
      }
      steps{
        sh '''
          #!/bin/bash
          echo "hello this is a test $ABC $cp cc"
          '''
      }
    }
  }
}