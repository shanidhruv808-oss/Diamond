# 🚀 DiamondVault Deployment Guide

## 📋 Files Created for Deployment

✅ **requirements.txt** - Python dependencies
✅ **Procfile** - Render process configuration  
✅ **build.sh** - Build and migration script
✅ **.gitignore** - Files to exclude from Git
✅ **production_settings.py** - Production-specific settings
✅ **settings.py** - Updated with environment support

## 🔧 Environment Variables Needed for Render

```
# Database
DATABASE_URL=postgresql://username:password@host:port/dbname

# Django
SECRET_KEY=your-long-secret-key-here
DEBUG=False

# Razorpay (Production)
RAZORPAY_KEY_ID=rzp_live_your_live_key
RAZORPAY_KEY_SECRET=your_live_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@diamondvault.com
```

## 🚀 Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Deploy on Render
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Name**: diamondvault
   - **Environment**: Python 3
   - **Branch**: main
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn DiamondVault.wsgi:application --bind 0.0.0.0:$PORT`

### 3. Add Environment Variables
Add all variables from above in Render dashboard

### 4. Deploy!
Click "Create Web Service" and Render will deploy automatically

## 🌐 Your Live Site
**URL**: https://diamondvault.onrender.com
**Admin**: https://diamondvault.onrender.com/admin/

## 📊 Post-Deployment Checklist
- [ ] Test user registration/login
- [ ] Test diamond browsing
- [ ] Test bidding system
- [ ] Test payment flow with live Razorpay keys
- [ ] Verify email notifications work
- [ ] Check automated winner declaration
- [ ] Monitor logs for errors

## 🔧 Troubleshooting

**Build Failed**: Check requirements.txt versions
**Database Error**: Verify DATABASE_URL format
**Static Files Missing**: Check STATIC_ROOT setting
**Payment Issues**: Use live Razorpay keys
**502 Error**: Check start command and port binding

## 📞 Support
- Render Docs: https://render.com/docs
- Django Deployment: https://render.com/docs/deploy-django
- Render Status: https://status.render.com
