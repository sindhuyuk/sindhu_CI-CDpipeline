pipeline {
    agent any

    stages {
        stage('GIT clone') {
            steps {
                echo 'get the code for git/git hub'
                // Get some code from a GitHub repository
                git 'https://github.com/sindhuyuk/sindhu_CI-CDpipeline.git'
            }
        } 
        stage('Maven Build') {
            steps {
                echo 'Building using maven command,pre-request docker should have java maven'
                // Run Maven on a Unix agent.
                sh "mvn -Dmaven.test.failure.ignore=true clean package"
            }
        }
         stage('Sonar Cube') {
            steps {
                echo 'this will check code errors & duplicates using sonar quality gates profile'
                echo 'step 2. withSonarQubeEnv(My SonarQube Server, envOnly: true)'
            }
        }
         stage('OWASP Security vulnerabilities check') {
            steps {
                echo 'step3: checks code vunarabilities'
            }
        }
         stage('Docker Build & push to docker hub') {
            steps {
                echo 'to build image(.jar file from above maven build stage)'
                echo 'next push our image to docker registry'
                echo 'step4 -->command: docker build - < Dockerfile'
                echo 'step5---> command: docker push imagename         sindhujava:latest'
            }
        }
         stage('Deploy Kuberneties/Docker/TomCat') {
            steps {
                echo 'The docker image code will be deployed into kuberneties'
                echo 'step 6---> command: docker run imagename(sindhu) : tagname(ex version)'
            }
        }
        stage('Testing application selinuem') {
            steps {
                echo 'now application is deployed and ready to access now ew can continew testing user id login passwrrod'
                echo 'step 6---> tester will give seliem script to here'
            }
        }
        post {
                // If Maven was able to run the tests, even if some of the test
                // failed, record the test results and archive the jar file.
                success {
                    junit '**/target/surefire-reports/TEST-*.xml'
                    archiveArtifacts 'target/*.jar'
                }
        }
    }
}


