pipeline {
    agent {
        docker {label 'linux'
        image 'muhammadqadora/jenkins-inbound-agent'
        args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
    stages {
        stage('Print users and parameters') {
            steps {
                println("=====================================${STAGE_NAME}=====================================")
            }
        }
        stage('Get Instance ip and id') {
            steps {
                println("=====================================${STAGE_NAME}=====================================")
                withCredentials([aws(accessKeyVariable: 'AWS_ACCESS_KEY_ID', credentialsId: 'Terraform-aws-creds', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    script {
                        env.instanceips = sh(script: '''
                        #!/bin/bash
                        instanceId="$(aws ec2 describe-instances \
                            --filters Name=tag:Name,Values=telegrambot --query "Reservations[*].Instances[?(@.State.Name == 'running')].InstanceId"  \
                            --region ap-northeast-1 --out text)"
                        if [ -z $instanceId ];then
                            exit 1
                        fi
                        ips=$(aws ec2 describe-instances \
                            --filters Name=tag:Name,Values=telegrambot --query "Reservations[*].Instances[?(@.State.Name == 'running')].PublicIpAddress"  \
                            --region ap-northeast-1 --out text)
                        echo $ips
                        ''',returnStdout: true).trim()
                    }
                }
            }
        }
        stage('docker login') {
            environment {
            c = credentials('dockerlogin')
            }
            steps {
                println("=====================================${STAGE_NAME}=====================================")
                script {
                sh '''
                #!/bin/bash
                echo $c_PSW | docker login --username $c_USR --password-stdin
                echo "Success!" 
                '''
                }
            }
        }
        stage('Deploy to target ec2') {
            steps {
                println("=====================================${STAGE_NAME}=====================================")
                withCredentials([sshUserPrivateKey(credentialsId: 'ec2-ssh-key', keyFileVariable: 'key_path', usernameVariable: 'ubuntu')]) {
                script {
                    copyArtifacts filter: 'TerraformOutput.txt', fingerprintArtifacts: true, projectName: 'Terraform', selector: lastSuccessful()
                    sh '''
                    #!/bin/bash
                    echo $instanceips
                    export REGION_NAME=$(grep '^region' TerraformOutput.txt | tr -d ' ' | sed 's/region=//')
                    echo $REGION_NAME
                    export GPT_TBL="openai-table-terraform"
                    echo $GPT_TBL
                    export TELEGRAM_APP_URL=$(grep '^domain_name' TerraformOutput.txt | tr -d ' ' | sed 's/domain_name=//')
                    echo $TELEGRAM_APP_URL
                    export SQS_URL=$(grep '^sqs_name' TerraformOutput.txt | tr -d ' ' | sed 's/sqs_name=//')
                    echo $SQS_URL
                    export SNS_ARN=$(grep '^sns_arn' TerraformOutput.txt | tr -d ' ' | sed 's/sns_arn=//')
                    export DYNAMO_TBL="predictions-table-terraform"
                    for i in $instanceips; do
                        ssh -o StrictHostKeyChecking=no -i $key_path ubuntu@$i \
                            "sudo docker rm telegrambot -f 2> /dev/null;
                             sudo docker pull muhammadqadora/telegrambot-aws-terraform:latest;
                             sudo docker run --name telegrambot -d -e REGION_NAME="$REGION_NAME" \
                                -e GPT_TBL="$GPT_TBL" -e TELEGRAM_APP_URL="$TELEGRAM_APP_URL" \
                                -e SQS_URL="$SQS_URL" \
                                -e SNS_ARN="$SNS_ARN" \
                                -e DYNAMO_TBL="$DYNAMO_TBL" \
                                -e SERVER_ENDPOINT="$TELEGRAM_APP_URL/sns_update" \
                                -p 5000:5000 muhammadqadora/telegrambot-aws-terraform:latest"
                    done
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