// EcoChain Exchange - Jenkins CI/CD Pipeline (AWS: ECR + EKS)
// BEFORE USE: replace <account-id> below with your 12-digit AWS account ID
 
pipeline {
    agent any
 
    environment {
        AWS_REGION    = 'eu-north-1'
        ECR_REGISTRY  = '636704811196.dkr.ecr.eu-north-1.amazonaws.com'
        ECR_REPO      = 'ecochain-app'
        IMAGE_TAG     = "${env.BUILD_NUMBER}"
        CLUSTER_NAME  = 'ecochain-eks'
        K8S_NAMESPACE = 'ecochain'
    }
 
    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
 
    stages {
 
        stage('Checkout') {
            steps {
                echo "Checking out source code from GitHub..."
                checkout scm
            }
        }
 
        stage('Install & Test') {
            steps {
                dir('app') {
                    sh '''
                        python3.13 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip -q
                        pip install -r requirements.txt -q
                        python -m compileall .
                        echo "Tests passed."
                    '''
                }
            }
        }
 
        stage('Build Docker Image') {
            steps {
                dir('app') {
                    sh """
                        docker build -t ${ECR_REPO}:${IMAGE_TAG} .
                        docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}
                        docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPO}:latest
                    """
                }
            }
        }
 
        stage('Push to ECR') {
            steps {
                sh """
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
 
                    docker push ${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/${ECR_REPO}:latest
                """
            }
        }
 
        stage('Deploy to EKS') {
            steps {
                sh """
                    aws eks update-kubeconfig \
                        --region ${AWS_REGION} \
                        --name ${CLUSTER_NAME}
 
                    kubectl apply -f k8s/namespace.yaml
                    kubectl apply -f k8s/configmap.yaml
                    kubectl apply -f k8s/secret.yaml
                    kubectl apply -f k8s/postgres.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl apply -f k8s/hpa.yaml
 
                    kubectl -n ${K8S_NAMESPACE} set image \
                        deployment/ecochain-app \
                        ecochain-app=${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}
 
                    kubectl -n ${K8S_NAMESPACE} rollout status \
                        deployment/ecochain-app --timeout=120s
                """
            }
        }
    }
 
    post {
        success {
            echo "Build #${env.BUILD_NUMBER} deployed to EKS successfully."
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed. Check console output above."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
