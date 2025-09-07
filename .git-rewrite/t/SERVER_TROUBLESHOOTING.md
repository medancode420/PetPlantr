# 🚨 PetPlantr Server Connection Troubleshooting

## Issue: "localhost refused to connect" / ERR_CONNECTION_REFUSED

This means the Next.js development server isn't running. Here's how to fix it:

## 🔧 **SOLUTION 1: Manual Server Start**

Open your terminal and run these commands:

```bash
# Navigate to the frontend directory
cd /Users/medan/Downloads/PetPlantr/frontend

# Install dependencies (if needed)
npm install

# Start the development server
npm run dev
```

**Expected output:**
```
▲ Next.js 15.4.4
- Local:        http://localhost:3000
- Environments: .env.local

✓ Starting...
✓ Ready in 2.3s
```

## 🔧 **SOLUTION 2: Use the Start Script**

```bash
cd /Users/medan/Downloads/PetPlantr/frontend
./start-server.sh
```

## 🔧 **SOLUTION 3: Try Different Port**

If port 3000 is busy:

```bash
cd /Users/medan/Downloads/PetPlantr/frontend
npx next dev -p 3001
```

Then visit: http://localhost:3001

## 🔧 **SOLUTION 4: Clean Start**

If you're having persistent issues:

```bash
cd /Users/medan/Downloads/PetPlantr/frontend

# Clean everything
rm -rf .next
rm -rf node_modules

# Reinstall and restart
npm install
npm run dev
```

## 🔧 **SOLUTION 5: Check for Conflicts**

Check if something is using port 3000:

```bash
# Check what's using port 3000
lsof -i :3000

# Kill any processes using port 3000
lsof -ti:3000 | xargs kill -9
```

## 🎯 **What Should Happen**

Once the server starts successfully, you should see:

1. **Terminal output** showing "Ready in X.Xs"
2. **Browser access** to http://localhost:3000 (or 3001, 3002, etc.)
3. **PetPlantr homepage** loads with navigation and upload button
4. **SystemStatus component** shows green checkmarks
5. **No console errors** in browser dev tools

## 🔍 **Common Issues & Fixes**

### Issue: "EADDRINUSE: address already in use"
**Fix:** Use a different port: `npx next dev -p 3001`

### Issue: "Module not found" errors
**Fix:** Run `npm install` to ensure all dependencies are installed

### Issue: Build errors
**Fix:** 
```bash
rm -rf .next
npm run build
npm run dev
```

### Issue: Permission denied
**Fix:** `chmod +x start-server.sh`

## 📞 **Still Having Issues?**

If none of these work, try:

1. **Restart your terminal completely**
2. **Check if Node.js is installed**: `node --version`
3. **Check if npm is working**: `npm --version`
4. **Try the build command first**: `npm run build`

## ✅ **Success Indicators**

You'll know it's working when:
- Terminal shows "Ready in X.Xs"
- Browser loads http://localhost:3000 without errors
- You can see the PetPlantr homepage
- Upload button is clickable
- SystemStatus component appears at the bottom

**Once you see these, your application is running correctly!** 🎉
