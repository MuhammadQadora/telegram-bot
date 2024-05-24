FROM ubuntu as installer

#Install AWS CLI
RUN apt update \
    && apt-get install python3 python3-pip curl wget unzip gnupg software-properties-common -y \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install --bin-dir /aws-cli-bin/

RUN wget https://releases.hashicorp.com/terraform/1.8.4/terraform_1.8.4_linux_amd64.zip \
    && unzip terraform_1.8.4_linux_amd64.zip \
    && mv terraform /usr/local/bin/

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

RUN mkdir /snyk && cd /snyk \
    && curl https://static.snyk.io/cli/v1.666.0/snyk-linux -o snyk \
    && chmod +x ./snyk

FROM jenkins/inbound-agent
USER root
RUN apt-get update && apt install python3-pip -y
COPY --from=docker /usr/local/bin/docker /usr/local/bin/
COPY --from=installer /usr/local/aws-cli/ /usr/local/aws-cli/
COPY --from=installer /aws-cli-bin/ /usr/local/bin/
COPY --from=installer /snyk/ /usr/local/bin/
COPY --from=installer /usr/local/bin/terraform /usr/local/bin/
COPY --from=installer /usr/local/bin/kubectl /usr/local/bin/
USER jenkins