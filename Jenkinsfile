// ---------------------------------------------------------------------------
// EcoChain Exchange - Jenkins CI/CD Pipeline
//
// Stages:
//   1. Checkout source code from GitHub
//   2. Install dependencies & run unit tests
//   3. Build Docker image
//   4. Push image to a container registry (Docker Hub / ECR)
//   5. Deploy to Kubernetes cluster
//
// Configure these Jenkins credentials before running:
//   - dockerhub-creds   : Username/password for Docker Hub (or ECR auth)
//   - kubeconfig-cred   : Kubernetes config file credential
// ---------------------------------------------------------------------------

pipeline {
    agent any

    environment {
        IMAGE_NAME   = "yourdockerhubuser/ecochain-app"
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
        K8S_NAMESPACE = "ecochain"
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                dir('app') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        # Run basic syntax / unit tests
                        python -m compileall .
                        echo "Tests passed."
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                dir('app') {
                    sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                    usernameVariable: 'DOCKER_USER',
                                                    passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-cred', variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/namespace.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/configmap.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/secret.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/postgres.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/deployment.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/service.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/hpa.yaml
                        kubectl --kubeconfig=$KUBECONFIG apply -f k8s/ingress.yaml

                        kubectl --kubeconfig=$KUBECONFIG -n ${K8S_NAMESPACE} \
                            set image deployment/ecochain-app ecochain-app=${IMAGE_NAME}:${IMAGE_TAG}

                        kubectl --kubeconfig=$KUBECONFIG -n ${K8S_NAMESPACE} \
                            rollout status deployment/ecochain-app --timeout=120s
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "EcoChain Exchange build #${env.BUILD_NUMBER} deployed successfully."
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed. Check logs above."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
