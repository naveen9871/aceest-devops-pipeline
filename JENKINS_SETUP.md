# Jenkins Local Integration Setup (Assignment Submission Guide)

This guide provides exactly how to spin up a local Jenkins server directly from this repository to simulate a production build gate and capture the necessary screenshots for your DevOps Assignment.

## 1. Start the Jenkins Local Server
We've created a custom Dockerfile for Jenkins (`Dockerfile.jenkins`) that pre-installs Python 3 so your pipeline works out-of-the box.

1. Open a new terminal inside this repository folder.
2. Run the following command to start Jenkins using docker compose:
   ```bash
   docker compose -f docker-compose.jenkins.yml up --build -d
   ```
3. To get the Initial Admin Password required to unlock Jenkins, run:
   ```bash
   docker logs aceest-devops-pipeline-jenkins-1 2>&1 | grep "Please use the following password" -A 2
   ```
   *(Copy the 32-character string it spits out).*

## 2. Configure the Jenkins Server
1. Open your web browser and navigate to: [http://localhost:8080](http://localhost:8080)
2. **Unlock Jenkins**: Paste the password you copied from the logs.
3. **Customize Jenkins**: Click **"Install suggested plugins"**. Wait for this to finish (this simulates installing Git, Pipeline, etc.).
4. **Admin User**: Either create an admin user or click "Skip and continue as admin".

## 3. Create & Run the Pipeline
1. On the Jenkins Dashboard left-hand sidebar, click **"New Item"**.
2. **Name it**: `aceest-fitness-build-pipeline`
3. Click **"Pipeline"** and then hit **OK**.
4. Scroll down to the **Pipeline** section.
5. In the **Definition** dropdown, select **"Pipeline script from SCM"**.
6. **SCM dropdown**: Select **Git**.
7. **Repository URL**: Enter your GitHub Repository URL (e.g. `https://github.com/naveen9871/aceest-devops-pipeline.git`).
8. Ensure **Script Path** says `Jenkinsfile` (this already matches our repo!).
9. Click **Save**.
10. Click **"Build Now"** on the left menu.

## 4. Capture Submit Screenshots
Take screenshots of the following elements to prove the build works for grading:
- **Screenshot 1 (The Configuration)**: A screenshot showing the "Pipeline from SCM" and the Repository URL pointing to your Github repo.
- **Screenshot 2 (The Successful Build)**: The Stage View after the pipeline runs successfully (It should show stages like "Checkout", "Clean Build & Quality Gate" in Green).
- **Screenshot 3 (The Logs)**: Click on the green successful build number (e.g. #1), click **"Console Output"** and take a screenshot of the bottom where it says `Finished: SUCCESS` along with the Pytest passing output!

## 5. Cleanup
To shut down and remove the Jenkins server once you're done taking screenshots:
```bash
docker compose -f docker-compose.jenkins.yml down -v
```
