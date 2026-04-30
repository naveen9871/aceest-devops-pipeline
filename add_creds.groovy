import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*
import hudson.util.Secret
import java.nio.file.Files
import java.nio.file.Paths

def domain = Domain.global()
def store = Jenkins.instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

// Add kubeconfig-credentials
def kubeConfigPath = "/var/jenkins_home/kubeconfig"
def kubeConfigBytes = Files.readAllBytes(Paths.get(kubeConfigPath))
def kubeCred = new SecretBytes(
    CredentialsScope.GLOBAL,
    "kubeconfig-credentials",
    "Minikube Config",
    SecretBytes.fromBytes(kubeConfigBytes)
)
store.addCredentials(domain, kubeCred)

// Add dockerhub-credentials (using placeholders if unknown, but user should update)
def dockerCred = new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "dockerhub-credentials",
    "Docker Hub Credentials",
    "naveen9871",
    "DUMMY_PASSWORD" 
)
store.addCredentials(domain, dockerCred)

println "Credentials added successfully"
