# GitHub Actions Setup Guide

This guide will help you configure your GitHub repository to run the backend container using GitHub Actions.

## Prerequisites

1. A GitHub repository with your finance-assist code
2. Required API keys and credentials

## Step 1: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → Secrets

Add the following **Repository Secrets**:

### Required Secrets:
- `OPENAI_API_KEY` - Your OpenAI API key
- `UNSTRUCTURED_API_KEY` - Your Unstructured API key (optional)
- `LLAMAPARSE_API_KEY` - Your LlamaParse API key (optional)
- `SECRET_KEY` - Django secret key (optional, will use default if not provided)

### How to add secrets:
1. Click "New repository secret"
2. Enter the name (e.g., `OPENAI_API_KEY`)
3. Enter the value
4. Click "Add secret"

## Step 2: Configure GitHub Variables (Optional)

Go to your GitHub repository → Settings → Secrets and variables → Actions → Variables

Add the following **Repository Variables** (these have defaults):

- `OPENAI_MODEL_NAME` = `gpt-4o-mini`
- `OPENAI_EMBEDDING_MODEL` = `text-embedding-3-small`
- `OPENAI_TEMPERATURE` = `0.1`
- `OPENAI_MAX_TOKENS` = `4096`

## Step 3: Workflow Files

Two workflow files have been created:

### 1. `.github/workflows/backend-deploy.yml` (Advanced)
- Builds and pushes Docker images to GitHub Container Registry
- More complex but provides better container management
- Good for production-like deployments

### 2. `.github/workflows/backend-simple.yml` (Recommended)
- Uses docker-compose for simpler setup
- Easier to debug and modify
- Better for development and testing

## Step 4: Enable GitHub Actions

1. Go to your repository's "Actions" tab
2. You should see the workflows listed
3. Click on "Deploy Backend (Simple)" workflow
4. Click "Run workflow" to test it manually

## Step 5: Monitor the Deployment

1. Go to the "Actions" tab
2. Click on your workflow run
3. Monitor the logs in real-time
4. Check for any errors or issues

## Workflow Triggers

The workflows will run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Manual trigger via "Run workflow" button

## Services Provided

When the workflow runs successfully, you'll have:

- **Backend API**: Available at `http://localhost:8000`
- **Django Admin**: Available at `http://localhost:8000/admin/`
- **Database**: MySQL 8.0 with finance_assist database
- **Default Admin User**: 
  - Username: `admin`
  - Password: `admin123`

## Troubleshooting

### Common Issues:

1. **Missing API Keys**: Make sure all required secrets are configured
2. **Database Connection**: The workflow waits for MySQL to be ready
3. **Port Conflicts**: The workflow uses ports 8000 and 3306
4. **Memory Issues**: GitHub Actions runners have limited resources

### Debug Steps:

1. Check the workflow logs in the Actions tab
2. Look for specific error messages
3. Verify all secrets are properly configured
4. Test the docker-compose setup locally first

## Local Testing

Before pushing to GitHub, test locally:

```bash
# Copy environment variables
cp backend/env.example .env

# Edit .env with your actual API keys
# Then run:
docker-compose -f docker-compose.ci.yml up --build
```

## Next Steps

Once the GitHub Actions workflow is working:

1. **AWS Deployment**: Modify the workflow to deploy to AWS
2. **Environment Management**: Set up different environments (dev, staging, prod)
3. **Monitoring**: Add health checks and monitoring
4. **Security**: Implement proper secret management
5. **Scaling**: Configure auto-scaling for production

## Security Notes

- Never commit API keys or secrets to the repository
- Use GitHub Secrets for sensitive information
- Consider using different API keys for different environments
- Regularly rotate your API keys
- Monitor usage and costs

## Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Verify your API keys are valid
3. Test the docker-compose setup locally
4. Review the Django settings configuration



