@Library("teckdigital") _
def appName = "scan-server"
pipeline {
   agent {
    kubernetes {
        inheritFrom "kaniko-template"
    }
  }
    
    stages {
        stage('Build and Tag Image') {
            steps {
                container('kaniko') {
                    script {
                        buildDockerImage(additionalImageTags: ["latest"], imageName: "shelf-mate/scan-server")
                    }
                }
            }
        }
    }
}