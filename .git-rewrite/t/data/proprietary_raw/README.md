# PetPlantr Photo Collection Guide

## 📸 Proprietary Multi-View Pet Photos

### Required Structure
```
data/proprietary_raw/
├── pet_001_golden_retriever/
│   ├── front.jpg     # Pet facing camera directly
│   ├── left.jpg      # Pet's left side profile  
│   ├── right.jpg     # Pet's right side profile
│   └── back.jpg      # Pet from behind
├── pet_002_labrador/
│   ├── front.jpg
│   ├── left.jpg
│   ├── right.jpg
│   └── back.jpg
└── ... (need 5 complete pets minimum)
```

### Photo Requirements
- **Resolution**: 1024x1024+ preferred
- **Format**: JPEG (.jpg)
- **Background**: Plain/simple (white wall ideal)
- **Lighting**: Natural window light preferred
- **Pet Position**: Clear view, no obstructions
- **Quality**: Sharp focus, good contrast

### Quick Collection Tips
1. **Use burst mode** for moving pets
2. **Get help** - one person holds treats, other takes photos
3. **Take extras** - capture 2-3 shots per angle
4. **Check focus** before moving to next angle
5. **Phone camera is fine** - modern phones work great

### Processing Commands
```bash
# 1. After collecting photos:
python scripts/preprocess_proprietary.py

# 2. Upload to S3:
bash scripts/process_and_upload.sh

# 3. Start Stage 2 training:
modal run train_unet_stage2.py --env BATCH=1,GRAD_ACCUM=8,EPOCHS=5
```

### Status Check
```bash
# Check collection progress:
node performance-test.js | grep "Proprietary Photo Collection"

# Manual check:
ls -la data/proprietary_raw/*/
```

## 🎯 Current Progress

**Folders Created:**
- ✅ pet_001_golden_retriever/
- ✅ pet_002_labrador/  
- ✅ pet_003_beagle/
- ✅ pet_004_british_shorthair/
- ✅ pet_005_persian_cat/

**Photos Needed:** 20 total (4 views × 5 pets)

**Status:** Ready for photo collection! 📸
