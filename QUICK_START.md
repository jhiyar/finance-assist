# Quick Start: GitHub Actions Backend Deployment

## 🚀 Get Started in 5 Minutes

### 1. Configure GitHub Secrets
Go to your repo → Settings → Secrets and variables → Actions → Secrets

**Add these secrets:**
- `OPENAI_API_KEY` (required)
- `UNSTRUCTURED_API_KEY` (optional)
- `LLAMAPARSE_API_KEY` (optional)
- `SECRET_KEY` (optional)

### 2. Push to GitHub
```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push origin main
```

### 3. Check Actions Tab
- Go to your repo's "Actions" tab
- You should see "Deploy Backend (Simple)" workflow
- Click on it to see the progress



## 📋 What You Get

When the workflow runs successfully:
- ✅ Backend API at `http://localhost:8000`
- ✅ Django Admin at `http://localhost:8000/admin/`
- ✅ MySQL database with finance_assist schema
- ✅ Default admin user (admin/admin123)

## 🔧 Workflow Files

- **`backend-simple.yml`** - Recommended (uses docker-compose)
- **`backend-deploy.yml`** - Advanced (builds Docker images)

## 🆘 Troubleshooting

**Workflow fails?**
1. Check Actions tab for error logs
2. Verify all secrets are configured
3. Test locally with `./test-local-setup.sh`

**Need help?**
- Check `GITHUB_SETUP.md` for detailed instructions
- Review the workflow logs in GitHub Actions

## 🎯 Next Steps

Once working on GitHub:
1. Modify workflow to deploy to AWS
2. Set up different environments
3. Add monitoring and health checks
4. Configure auto-scaling
