# Week 8 Comparison: VM Deployment vs Cloud Run

## Deployment Comparison

| Area | Week 3-5 VM/Docker/SSH approach | Week 8 Artifact Registry/Cloud Run/Terraform approach |
| --- | --- | --- |
| Build location | The container image was built manually or on the VM after files were copied over SSH. | GitHub Actions builds the image from the repository and tags it with the commit SHA. |
| Image storage | Images lived on individual VMs, so each host had its own local Docker image cache. | Images are pushed to Artifact Registry in a central repository named `cis410-app`. |
| Deployment trigger | Deployment depended on manually running SSH commands or pushing to VM-specific workflows. | A push to `main` runs the `Deploy to Cloud Run` workflow automatically. |
| Infrastructure management | VM networking and host setup required more manual care, including Docker installation and SSH access. | Terraform manages Artifact Registry, Cloud Run, public invoker IAM, and service settings. |
| Scaling | Scaling required adding or resizing VM instances and managing more hosts. | Cloud Run scales container instances automatically based on request traffic. |
| Availability | If a VM failed or Docker stopped, the app could become unavailable until the host was repaired. | Cloud Run runs the service on managed Google infrastructure and replaces instances automatically. |
| Security boundary | SSH keys, open VM ports, host patching, and Docker daemon access were operational concerns. | OIDC gives GitHub short-lived cloud access, and the app is exposed through HTTPS Cloud Run instead of SSH-managed hosts. |
| Rollback and traceability | Rollbacks required knowing which image or files were on a VM and manually redeploying. | Each deployment uses an immutable commit SHA image tag, making the deployed version easy to identify. |

## Reflection Questions

1. Why is Artifact Registry useful in this deployment?

Artifact Registry gives the project a central place to store trusted Docker images. Tagging the `flask-app` image with the commit SHA connects the running Cloud Run service back to the exact GitHub revision that built it.

2. What does Cloud Run improve compared with the VM deployment?

Cloud Run removes the need to maintain Docker hosts, SSH into servers, restart containers, or patch VM operating systems for this app. It also provides a managed HTTPS endpoint and automatic scaling, which makes the deployment simpler and more repeatable.

3. How does Terraform help in this lab?

Terraform records the desired cloud resources in source code instead of relying on console clicks. The `terraform/week8` configuration makes the Artifact Registry repository, Cloud Run service, IAM policy, and outputs reproducible through the CI/CD pipeline.

4. Why is OIDC better than storing a long-lived service account key?

OIDC lets GitHub Actions exchange its workflow identity for short-lived Google Cloud credentials at runtime. That avoids storing a downloadable service account key in GitHub secrets, reducing the impact if repository secrets or logs are exposed.
