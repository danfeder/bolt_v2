"""
Constraint API Routes

This module provides API endpoints for accessing constraint information,
including categories, compatibility rules, and constraint metadata.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..scheduling.abstractions.constraint_factory import get_constraint_factory, ConstraintInfo
from ..scheduling.abstractions.constraint_manager import EnhancedConstraintManager

router = APIRouter(prefix="/api/constraints", tags=["constraints"])


class ConstraintMetadata(BaseModel):
    """Constraint metadata for API responses"""
    name: str
    description: str
    category: str
    default_enabled: bool
    default_weight: Optional[int] = None
    is_relaxable: bool
    incompatible_with: List[str]
    requires: List[str]


class ConstraintCategory(BaseModel):
    """Category information for API responses"""
    name: str
    description: str
    constraints: List[ConstraintMetadata]


@router.get("/categories", response_model=List[ConstraintCategory])
async def get_constraint_categories():
    """
    Get all constraint categories with their constraints
    
    Returns a list of all constraint categories and the constraints within each category.
    """
    factory = get_constraint_factory()
    
    # Group constraints by category
    categories: Dict[str, List[ConstraintMetadata]] = {}
    
    # Category descriptions (hardcoded for now, could be made dynamic)
    category_descriptions = {
        "assignment": "Constraints related to class assignments and scheduling",
        "instructor": "Constraints related to instructor workload and preferences",
        "student": "Constraints related to student experience and learning",
        "facility": "Constraints related to facility usage and availability",
        "general": "General scheduling constraints that don't fit other categories" 
    }
    
    # Collect all constraints and group by category
    for name, info in factory.get_all_constraint_info().items():
        category = info.category
        
        if category not in categories:
            categories[category] = []
        
        # Convert to API model
        constraint_metadata = ConstraintMetadata(
            name=info.name,
            description=info.description,
            category=info.category,
            default_enabled=info.default_enabled,
            default_weight=info.default_weight,
            is_relaxable=info.is_relaxable,
            incompatible_with=list(info.incompatible_with),
            requires=list(info.requires)
        )
        
        categories[category].append(constraint_metadata)
    
    # Convert to list of category objects
    result = []
    for category_name, constraints in categories.items():
        result.append(ConstraintCategory(
            name=category_name,
            description=category_descriptions.get(category_name, f"Constraints in {category_name} category"),
            constraints=constraints
        ))
    
    return result


@router.get("/{constraint_name}", response_model=ConstraintMetadata)
async def get_constraint_info(constraint_name: str):
    """
    Get detailed information about a specific constraint
    
    Args:
        constraint_name: The name of the constraint
        
    Returns:
        Detailed information about the constraint
    """
    factory = get_constraint_factory()
    info = factory.get_constraint_info(constraint_name)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"Constraint {constraint_name} not found")
    
    return ConstraintMetadata(
        name=info.name,
        description=info.description,
        category=info.category,
        default_enabled=info.default_enabled,
        default_weight=info.default_weight,
        is_relaxable=info.is_relaxable,
        incompatible_with=list(info.incompatible_with),
        requires=list(info.requires)
    )
