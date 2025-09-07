"""
LangChain Validation Agent for PetPlantr
========================================
Vets each rendered image & STL mesh before production.
"""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Any, Dict, List

import boto3
import numpy as np
import PIL.Image as Image
import trimesh
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import SystemMessage
from langchain.tools import StructuredTool

# 🔑 credentials pulled at runtime (Secrets Manager / env)
S3_BUCKET = os.environ.get("MODEL_BUCKET", "petplantr-outputs")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

s3 = boto3.client("s3")


# ---------- Image-side quality checks ---------- #
def _download_image(key: str) -> Image.Image:
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return Image.open(io.BytesIO(obj["Body"].read())).convert("RGB")


def clip_likeness_score(img: Image.Image, ref: Image.Image) -> float:
    """
    Placeholder – you'd plug in CLIP or your fine-tuned encoder here.
    Return cosine similarity in [0–1].
    """
    return 0.73  # TODO: real model


def blur_metric(img: Image.Image) -> float:
    """
    Simple variance of Laplacian as blur measure.
    """
    import cv2  # imported lazily on Lambda

    arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(arr, cv2.CV_64F).var()


# ---------- Mesh-side quality checks ---------- #
def _download_stl(key: str) -> trimesh.Trimesh:
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return trimesh.load(io.BytesIO(obj["Body"].read()), file_type="stl")


def manifold_ratio(mesh: trimesh.Trimesh) -> float:
    return mesh.is_watertight * 1.0  # 1 if watertight else 0


def face_count(mesh: trimesh.Trimesh) -> int:
    return len(mesh.faces)


# ---------- LangChain tools ---------- #
def validate_photo(key: str, ref_key: str) -> Dict[str, Any]:
    img = _download_image(key)
    ref = _download_image(ref_key)
    score = clip_likeness_score(img, ref)
    blur = blur_metric(img)
    return {
        "likeness_score": score,
        "blur_metric": blur,
        "pass": score >= 0.70 and blur >= 150.0,
    }


def validate_mesh(key: str) -> Dict[str, Any]:
    mesh = _download_stl(key)
    ratio = manifold_ratio(mesh)
    faces = face_count(mesh)
    return {
        "manifold_ratio": ratio,
        "faces": faces,
        "pass": ratio == 1.0 and faces <= 250_000,
    }


ImageTool = StructuredTool.from_function(
    validate_photo,
    name="ValidatePhotoQuality",
    description=(
        "Check likeness (CLIP) & blur metric for an uploaded buffered jpg/png. "
        "Inputs: { 'key': s3_key, 'ref_key': reference_key }"
    ),
)

MeshTool = StructuredTool.from_function(
    validate_mesh,
    name="ValidateMeshQuality",
    description=(
        "Ensure STL is watertight and under face-count budget. "
        "Input: { 'key': s3_key_to_stl }"
    ),
)

SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are PetPlantr's QA agent. Use the provided tools ONLY. "
        "Return JSON: {'photo_pass': bool, 'mesh_pass': bool, 'reasons': [...]}."
    )
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    openai_api_key=OPENAI_API_KEY,
)

agent = initialize_agent(
    tools=[ImageTool, MeshTool],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    system_message=SYSTEM_PROMPT,
)

# -------- Lambda handler wrapper -------- #
def handler(event, _ctx=None):
    """
    Lambda entry. Expects event:
      {
        "image_key": "uploads/pet123/front.jpg",
        "reference_key": "uploads/pet123/front.jpg",
        "stl_key": "stl_ready/pet123.stl"
      }
    """
    image_key = event["image_key"]
    ref_key = event["reference_key"]
    stl_key = event["stl_key"]

    query = (
        f"""Validate photo '{image_key}' vs reference '{ref_key}', then STL '{stl_key}'."""
    )
    result = agent(query)
    return json.loads(result["output"])


# -------- Local testing interface -------- #
def validate_local_files(image_path: str, stl_path: str) -> Dict[str, Any]:
    """
    Local validation for development and testing
    """
    try:
        # Validate image
        img = Image.open(image_path).convert("RGB")
        blur = blur_metric(img)
        
        # Validate mesh
        mesh = trimesh.load(stl_path)
        ratio = manifold_ratio(mesh)
        faces = face_count(mesh)
        
        photo_pass = blur >= 150.0
        mesh_pass = ratio == 1.0 and faces <= 250_000
        
        reasons = []
        if not photo_pass:
            reasons.append(f"Image blur metric too low: {blur:.1f} < 150.0")
        if ratio != 1.0:
            reasons.append(f"Mesh not watertight: {ratio:.1f}")
        if faces > 250_000:
            reasons.append(f"Too many faces: {faces:,} > 250,000")
            
        return {
            "photo_pass": photo_pass,
            "mesh_pass": mesh_pass,
            "overall_pass": photo_pass and mesh_pass,
            "reasons": reasons,
            "metrics": {
                "blur_metric": blur,
                "manifold_ratio": ratio,
                "face_count": faces
            }
        }
        
    except Exception as e:
        return {
            "photo_pass": False,
            "mesh_pass": False,
            "overall_pass": False,
            "reasons": [f"Validation error: {str(e)}"],
            "metrics": {}
        }


if __name__ == "__main__":
    # Test with local files
    import sys
    
    if len(sys.argv) >= 3:
        image_path = sys.argv[1]
        stl_path = sys.argv[2]
        
        print("🔍 PetPlantr Validation Agent - Local Test")
        print("=" * 50)
        
        result = validate_local_files(image_path, stl_path)
        
        print(f"📸 Photo validation: {'✅ PASS' if result['photo_pass'] else '❌ FAIL'}")
        print(f"🎯 Mesh validation: {'✅ PASS' if result['mesh_pass'] else '❌ FAIL'}")
        print(f"🎉 Overall result: {'✅ PASS' if result['overall_pass'] else '❌ FAIL'}")
        
        if result['metrics']:
            print(f"\n📊 Metrics:")
            print(f"   Blur metric: {result['metrics'].get('blur_metric', 0):.1f}")
            print(f"   Manifold ratio: {result['metrics'].get('manifold_ratio', 0):.1f}")
            print(f"   Face count: {result['metrics'].get('face_count', 0):,}")
        
        if result['reasons']:
            print(f"\n⚠️  Issues:")
            for reason in result['reasons']:
                print(f"   • {reason}")
    else:
        print("Usage: python validation_agent.py <image_path> <stl_path>")
