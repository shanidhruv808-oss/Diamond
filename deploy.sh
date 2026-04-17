#!/usr/bin/env bash
echo "🚀 Deploying DiamondVault to Render..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - Ready for deployment"
    echo "⚠️  Don't forget to:"
    echo "   1. Create GitHub repository"
    echo "   2. Add remote: git remote add origin https://github.com/yourusername/DiamondVault.git"
    echo "   3. Push: git push -u origin main"
else
    echo "📦 Committing changes..."
    git add .
    git commit -m "Deployment updates - $(date)"
    git push origin main
    echo "✅ Pushed to GitHub - Render will auto-deploy!"
fi

echo ""
echo "🌐 Next Steps:"
echo "1. Go to https://render.com"
echo "2. Connect your GitHub repository"
echo "3. Configure environment variables (see DEPLOY.md)"
echo "4. Deploy! Your site will be live at: https://diamondvault.onrender.com"
echo ""
echo "📋 Don't forget to:"
echo "- Add live Razorpay keys (not test keys)"
echo "- Configure database on Render"
echo "- Set up email for notifications"
echo "- Monitor logs after deployment"
