"""Tests for Google Maps & Places (New) integration and A2UI formatting."""

import pytest
from fastapi.testclient import TestClient
from workout_coach.core.maps_service import GoogleMapsService
from workout_coach.agent.tools import WorkoutCoachTools
from workout_coach.core.repository import WorkoutRepository
from workout_coach.api.main import app

client = TestClient(app)


def test_maps_service_fallback_search():
    """Verify GoogleMapsService returns realistic venues and live Google Maps links."""
    svc = GoogleMapsService()
    res = svc.search_fitness_facilities(location="Austin, TX", facility_type="gym")

    assert res["status"] == "success"
    assert res["location"] == "Austin, TX"
    assert res["facility_type"] == "gym"
    assert len(res["venues"]) > 0

    first_venue = res["venues"][0]
    assert "Austin" in first_venue["name"]
    assert "https://www.google.com/maps/search/" in first_venue["google_maps_url"]
    assert "https://www.google.com/maps/dir/" in first_venue["directions_url"]
    assert first_venue["rating"] >= 4.0


def test_maps_service_running_track():
    """Verify GoogleMapsService categorizes running tracks accurately."""
    svc = GoogleMapsService()
    res = svc.search_fitness_facilities(location="Seattle, WA", facility_type="running track")

    assert res["status"] == "success"
    first = res["venues"][0]
    assert "Track" in first["name"] or "Running" in first["name"] or "Trail" in first["name"]


def test_maps_a2ui_surface_generation():
    """Verify A2UI v0.8 surface generation from venues."""
    svc = GoogleMapsService()
    res = svc.search_fitness_facilities(location="Chicago, IL", facility_type="gym")
    a2ui = svc.build_a2ui_surface(res["venues"], "Chicago, IL", "gym")

    assert isinstance(a2ui, list)
    assert len(a2ui) == 2
    assert "beginRendering" in a2ui[0]
    assert a2ui[0]["beginRendering"]["root"] == "root_card"
    assert "surfaceUpdate" in a2ui[1]

    components = a2ui[1]["surfaceUpdate"]["components"]
    comp_ids = [c["id"] for c in components]
    assert "header_title" in comp_ids
    assert "main_col" in comp_ids
    assert "root_card" in comp_ids


def test_coach_tools_find_nearby_gyms():
    """Verify WorkoutCoachTools find_nearby_gyms tool executes correctly."""
    repo = WorkoutRepository()
    tools = WorkoutCoachTools(repo)
    res = tools.find_nearby_gyms(location="Denver, CO", facility_type="gym")
    assert res["status"] == "success"
    assert len(res["venues"]) > 0


def test_api_maps_facilities_endpoint():
    """Verify GET /api/v1/maps/facilities endpoint."""
    res = client.get("/api/v1/maps/facilities?location=Miami,%20FL&facility_type=calisthenics%20park")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["venues"]) > 0
    assert "Miami" in data["venues"][0]["name"]
