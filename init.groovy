import jenkins.model.*
import hudson.security.*
import hudson.plugins.git.*
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition

def instance = Jenkins.getInstance()

// Create an admin user to prevent anonymous locks
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin")
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()

// Create pipeline
def jobName = "aceest-fitness-build-pipeline"
def job = instance.getItem(jobName)
if (job == null) {
  job = instance.createProject(WorkflowJob.class, jobName)
}

def scm = new GitSCM("https://github.com/naveen9871/aceest-devops-pipeline.git")
scm.branches = [new BranchSpec("*/main")]

def flowDefinition = new CpsScmFlowDefinition(scm, "Jenkinsfile")
flowDefinition.setLightweight(true)
job.setDefinition(flowDefinition)

job.save()
instance.save()
