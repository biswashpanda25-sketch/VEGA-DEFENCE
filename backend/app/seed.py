"""Idempotent synthetic demonstration dataset — VEGA SOVEREIGN DEFENCE & MILITARY INTELLIGENCE.
EVERY record created here is synthetic and labelled as such. No real classified or operational data.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import (Organization, User, Dataset, Entity, Relationship, Case, Finding,
                     Document, Notification, Connector)
from .security import hash_password

SYNTH = "SYNTHETIC-DEFENCE-DEMO"

CLEARANCE_BY_ROLE = {"platform_admin": "PROTECTED", "org_admin": "RESTRICTED",
                     "data_admin": "RESTRICTED", "auditor": "RESTRICTED"}

DISTRICT_COORDS = {
    "Khordha": (20.18, 85.62), "Cuttack": (20.46, 85.88), "Puri": (19.81, 85.83),
    "Ganjam": (19.38, 84.83), "Sambalpur": (21.47, 83.97), "Dhenkanal": (20.67, 85.60),
    "Koraput": (18.81, 82.71),
}

# Records above INTERNAL clearance, so classification enforcement is demonstrable with real data.
CLASSIFIED_SEED = {
    "Relief Helicopter Pad KPK (Synthetic)": "RESTRICTED",
    "Substation K-17 (Synthetic)": "RESTRICTED",
    "Embankment Segment BBSR-07 (Synthetic)": "PROTECTED",
    "Forward Airbase Trishul FOB-04 (Synthetic)": "RESTRICTED",
    "Air Defence Radar Station Indra-II (Synthetic)": "PROTECTED",
    "Central Ammunition Depot CAD-09 (Synthetic)": "PROTECTED",
}


def _user(db, email, name, role, org, pw):
    u = db.query(User).filter(User.email == email).first()
    if u: return u
    u = User(email=email, full_name=name, role=role, organization_id=org.id,
             clearance=CLEARANCE_BY_ROLE.get(role, "INTERNAL"),
             hashed_password=hash_password(pw))
    db.add(u); db.flush()
    return u

def seed(db: Session):
    if db.query(Organization).filter(Organization.code == "ODISHA-DEMO").first():
        return {"status": "already_seeded"}

    oifd = Organization(name="Northern Tactical Command — Strategic Infrastructure Directorate (Synthetic)",
                        code="ODISHA-DEMO", type="command", state="Northern Sector", classification="INTERNAL")
    osdma = Organization(name="Eastern Maritime & Coastal Defence Cell (Synthetic)",
                         code="ODISHA-DISASTER", type="command", state="Eastern Sector", classification="INTERNAL")
    ids = Organization(name="Integrated Defence Staff HQ — Joint Operations (Synthetic)",
                       code="HQ-IDS", type="headquarters", state="Strategic Command", classification="PROTECTED")
    db.add_all([oifd, osdma, ids]); db.flush()

    # Core demonstration accounts (compatible with automated test suites and defence logins)
    _user(db, "admin@gotham-demo.in", "Command Administrator (HQ IDS)", "platform_admin", oifd, "Gotham@2026")
    _user(db, "analyst@gotham-demo.in", "Lead Intelligence Officer (Northern Cmd)", "analyst", oifd, "Gotham@2026")
    _user(db, "reviewer@gotham-demo.in", "Operations Reviewer — Flag Officer", "reviewer", oifd, "Gotham@2026")
    _user(db, "disaster@gotham-demo.in", "Maritime Tactical Analyst (Eastern Fleet)", "analyst", osdma, "Gotham@2026")

    # Defence call-sign aliases
    _user(db, "admin@vega-defence.in", "Command Administrator (HQ IDS)", "platform_admin", oifd, "Gotham@2026")
    _user(db, "intel@vega-defence.in", "Lead Intelligence Officer (Northern Cmd)", "analyst", oifd, "Gotham@2026")
    _user(db, "reviewer@vega-defence.in", "Operations Reviewer — Flag Officer", "reviewer", oifd, "Gotham@2026")
    _user(db, "maritime@vega-defence.in", "Maritime Tactical Analyst (Eastern Fleet)", "analyst", osdma, "Gotham@2026")

    ds_assets = Dataset(organization_id=oifd.id, name="Strategic Defence Asset Register FY26",
                        description="Simulated military infrastructure asset inventory and forward bases.",
                        source_type="file", source_org=SYNTH, classification="INTERNAL",
                        provenance={"source": SYNTH, "ingested_at": datetime.now(timezone.utc).isoformat(),
                                    "label": "All defence records synthetic"})
    ds_maint = Dataset(organization_id=oifd.id, name="Tactical Logistics & Ordnance Movement Logs FY25-26",
                       description="Simulated military logistics events, maintenance and supply movements.",
                       source_type="file", source_org=SYNTH, classification="INTERNAL",
                       provenance={"source": SYNTH, "label": "All defence records synthetic"})
    ds_weather = Dataset(organization_id=osdma.id, name="Early Warning Radar & Maritime Sensor Telemetry",
                         description="Simulated early warning telemetry and coastal tracking advisories.", source_type="api",
                         source_org=SYNTH, classification="INTERNAL",
                         provenance={"source": SYNTH, "label": "All defence records synthetic"})
    db.add_all([ds_assets, ds_maint, ds_weather]); db.flush()

    entities = [
        # Military organizations / Command directorates
        ("organization", "Odisha Works Department (Synthetic)", "Northern Sector Military Engineering & Infrastructure Works Department", "Khordha", "active", {"role": "engineering_corps"}),
        ("organization", "Odisha Relief & Disaster Cell (Synthetic)", "Joint Quick Reaction & Forward Supply Directorate", "Khordha", "active", {"role": "logistics_support"}),
        ("supplier", "Mahanadi Fabrication Works (Synthetic)", "Heavy Armour & Armoured Bridge Fabrication Contractor", "Cuttack", "active", {"clearance": "RESTRICTED"}),
        # Hardened facilities / Forward bases / Depots
        ("warehouse", "Central Ammunition Depot CAD-09 (Synthetic)", "Hardened subterranean munition and missile storage facility", "Sambalpur", "active", {"storage_type": "deep_bunker", "capacity_tons": 5000}),
        ("facility", "Strategic POL Fuel Reserve Depot SP-04 (Synthetic)", "Hardened petroleum, oil and lubricants strategic reserve", "Cuttack", "active", {"fuel_capacity_kl": 25000}),
        ("warehouse", "Cuttack Central Relief Warehouse (Synthetic)", "Central Ordnance & Ammunition Reserve Warehouse CAD-01", "Cuttack", "active", {"storage_type": "underground_hardened"}),
        ("warehouse", "Berhampur District Store (Synthetic)", "Forward Logistics & Ordnance Reserve Depot FLD-04", "Ganjam", "active", {"storage_type": "reinforced"}),
        ("facility", "Khordha Pumping Station 4 (Synthetic)", "Strategic Military Grid Water & Fuel Pump Station", "Khordha", "degraded", {"criticality": "high"}),
        ("facility", "Puri Coastal Shelter Cluster A (Synthetic)", "Coastal Rapid Response Base & Helo Facility Alpha", "Puri", "active", {"sensor_readiness": "ready"}),
        ("facility", "Forward Airbase Trishul FOB-04 (Synthetic)", "Frontline fighter operating base with hardened shelters", "Cuttack", "active", {"runway_ft": 9000, "squadron": "Mirage-2000"}),
        ("facility", "Air Defence Radar Station Indra-II (Synthetic)", "3D Early warning surveillance & target acquisition radar post", "Khordha", "active", {"radar_band": "S-Band", "range_km": 250}),
        # Assets & Strategic Chokepoints
        ("asset", "Substation K-17 (Synthetic)", "33/11 kV Hardened Military Grid Substation powering Command Nodes", "Khordha", "active", {"substation_kv": "33/11"}),
        ("asset", "Bridge Mahanadi-03 (Synthetic)", "Strategic River Crossing Bridge (MLC-70 Heavy Armour Transit Axis)", "Cuttack", "under_maintenance", {"capacity_tons": 70}),
        ("asset", "Embankment Segment BBSR-07 (Synthetic)", "Forward Perimeter Fortification & Hardened Embankment Segment BBSR-07", "Khordha", "degraded", {"fortification": "blast_reinforced"}),
        ("asset", "Water Treatment Unit GPL-2 (Synthetic)", "Tactical Potable Water Purification Plant GPL-2", "Ganjam", "active", {}),
        ("asset", "Road Segment SH-14 KM42 (Synthetic)", "Strategic Mechanized Transit Highway Corridor SH-14 KM42", "Dhenkanal", "active", {"route_class": "heavy_armour"}),
        ("asset", "Relief Helicopter Pad KPK (Synthetic)", "Forward High-Altitude Tactical Helipad KPK", "Koraput", "offline", {"altitude_ft": 3200}),
        # Tactical Combat & Logistics Vehicles
        ("vehicle", "Rescue Vehicle RV-11 (Synthetic)", "Armoured Quick Reaction Vehicle RV-11", "Cuttack", "active", {"armour_level": "STANAG-3"}),
        ("vehicle", "Supply Truck ST-08 (Synthetic)", "Heavy Tactical Ordnance Transport ST-08 (6x6)", "Sambalpur", "active", {"payload_tons": 10}),
        # Munitions & Tactical Inventory
        ("inventory_item", "Tarpaulin Sheets 200gsm (Synthetic)", "Tactical Camouflage & Weatherproof Sheets 200gsm (10,000 units)", "Cuttack", "low_stock", {"spec": "IR_shielded"}),
        ("inventory_item", "Water Purification Tablets (Synthetic)", "Field Chemical & Water Neutralization Inventory", "Ganjam", "active", {}),
        ("inventory_item", "Portable Generators 5kW (Synthetic)", "Hardened Field Command Generators 5kW Silent Diesel", "Cuttack", "active", {"fuel_type": "diesel"}),
        # Strategic Military Fortification Projects
        ("project", "Coastal Embankment Rehabilitation Phase II (Synthetic)", "Forward Perimeter Fortification & Blast Embankment Project Phase II", "Puri", "in_progress", {}),
        ("project", "District Warehouse Modernisation (Synthetic)", "Central Ordnance Depot Hardening & Automation Program", "Ganjam", "in_progress", {}),
    ]
    created = {}
    for etype, name, desc, district, status, extra in entities:
        exists = db.query(Entity).filter(Entity.organization_id == oifd.id, Entity.name == name).first()
        if exists: created[name] = exists; continue
        lat, lon = DISTRICT_COORDS.get(district, (20.3, 85.1))
        seed_vals = sum(ord(c) for c in name) % 97
        e = Entity(organization_id=oifd.id, entity_type=etype, name=name, description=desc,
                   district=district, state="Odisha", status=status, confidence=1.0, is_synthetic=True,
                   classification=CLASSIFIED_SEED.get(name, "INTERNAL"),
                   latitude=round(lat + (seed_vals - 48) / 900.0, 5),
                   longitude=round(lon + (seed_vals % 41 - 20) / 300.0, 5),
                   attributes={"source_file": "strategic_defence_asset_register_fy26.csv", "source_org": SYNTH,
                               "provenance": "imported", "label": "SYNTHETIC DEFENCE RECORD", **extra})
        db.add(e); db.flush(); created[name] = e

    E = created
    rels = [
        ("Substation K-17 (Synthetic)", "Odisha Works Department (Synthetic)", "managed_by", "confirmed", 0.99,
         "Asset register row 12 lists managing Works Department engineering corps", "Strategic Defence Asset Register FY26 · row 12"),
        ("Bridge Mahanadi-03 (Synthetic)", "Odisha Works Department (Synthetic)", "maintained_by", "confirmed", 0.97,
         "Tactical maintenance log entries name the engineering directorate", "Tactical Maintenance Logs · entry 44"),
        ("Embankment Segment BBSR-07 (Synthetic)", "Odisha Works Department (Synthetic)", "managed_by", "confirmed", 0.96,
         "Military asset register row 21 confirms perimeter ownership", "Strategic Defence Asset Register FY26 · row 21"),
        ("Cuttack Central Relief Warehouse (Synthetic)", "Odisha Relief & Disaster Cell (Synthetic)", "managed_by", "confirmed", 0.98,
         "Ordnance warehouse registry names the joint logistics cell", "Strategic Defence Asset Register FY26 · row 3"),
        ("Berhampur District Store (Synthetic)", "Odisha Relief & Disaster Cell (Synthetic)", "managed_by", "confirmed", 0.95,
         "Forward depot registry entry 2 confirms logistics administration", "Strategic Defence Asset Register FY26 · row 4"),
        ("Tarpaulin Sheets 200gsm (Synthetic)", "Cuttack Central Relief Warehouse (Synthetic)", "located_at", "imported", 0.93,
         "Camouflage and equipment inventory batch location record", "Tactical Maintenance Logs · stock line 7"),
        ("Water Purification Tablets (Synthetic)", "Berhampur District Store (Synthetic)", "located_at", "imported", 0.91,
         "Field inventory batch location verified in logistics manifest", "Tactical Maintenance Logs · stock line 9"),
        ("Portable Generators 5kW (Synthetic)", "Cuttack Central Relief Warehouse (Synthetic)", "located_at", "imported", 0.90,
         "Hardened generator batch location field", "Tactical Maintenance Logs · stock line 11"),
        ("Mahanadi Fabrication Works (Synthetic)", "Bridge Mahanadi-03 (Synthetic)", "supplied_by", "inferred", 0.72,
         "Supplier invoices reference heavy armour bridge components; procurement link inferred",
         "Tactical Maintenance Logs · invoices 3,7 (supplier match)"),
        ("Rescue Vehicle RV-11 (Synthetic)", "Odisha Relief & Disaster Cell (Synthetic)", "managed_by", "confirmed", 0.94,
         "Quick reaction fleet register entry confirms tactical assignment", "Strategic Defence Asset Register FY26 · row 31"),
        ("Supply Truck ST-08 (Synthetic)", "Berhampur District Store (Synthetic)", "associated_with", "inferred", 0.63,
         "Repeated convoy telemetry records to the forward store; logistics association inferred",
         "Tactical Maintenance Logs · trips 12-19"),
        ("Coastal Embankment Rehabilitation Phase II (Synthetic)", "Embankment Segment BBSR-07 (Synthetic)", "connected_to", "confirmed", 0.88,
         "Fortification project scope explicitly lists blast barrier segment BBSR-07", "Project charter (synthetic defence) §2"),
        ("Puri Coastal Shelter Cluster A (Synthetic)", "Odisha Relief & Disaster Cell (Synthetic)", "managed_by", "unverified", 0.40,
         "Referenced in single intelligence advisory; coastal station managing authority not corroborated", "Synthetic advisory 2026-05-11"),
        ("District Warehouse Modernisation (Synthetic)", "Berhampur District Store (Synthetic)", "connected_to", "confirmed", 0.92,
         "Fortification project scope lists forward logistics store", "Project charter (synthetic defence) §3"),
        ("Forward Airbase Trishul FOB-04 (Synthetic)", "Air Defence Radar Station Indra-II (Synthetic)", "radar_covers", "confirmed", 0.98,
         "3D Radar Indra-II coverage envelope encloses Forward Airbase Trishul airspace", "Air Defence Sector Overlay 2026"),
        ("Central Ammunition Depot CAD-09 (Synthetic)", "Forward Airbase Trishul FOB-04 (Synthetic)", "supplied_by", "confirmed", 0.94,
         "Underground ordnance pipeline and convoy corridor supply airbase missile reserves", "Strategic Logistics Directive §4"),
        ("Strategic POL Fuel Reserve Depot SP-04 (Synthetic)", "Forward Airbase Trishul FOB-04 (Synthetic)", "supplied_by", "confirmed", 0.96,
         "Hardened fuel pipeline and dedicated aviation tanker convoy supplying airbase jet fuel tanks", "Strategic Fuel Logistics Directive §7"),
    ]
    for s, t, rt, prov, conf, ev, ref in rels:
        if s not in E or t not in E: continue
        if db.query(Relationship).filter(Relationship.source_id == E[s].id,
                                         Relationship.target_id == E[t].id,
                                         Relationship.rel_type == rt).first():
            continue
        db.add(Relationship(organization_id=oifd.id, source_id=E[s].id, target_id=E[t].id,
                            rel_type=rt, provenance=prov, confidence=conf,
                            evidence=ev, source_ref=ref))

    case = Case(organization_id=oifd.id,
                title="Operation Readiness Review — Strategic Corridors & Forward Basing (Synthetic)",
                description="Assess strategic readiness of forward ammunition reserves, bridge crossing capacity and perimeter fortifications across tactical sectors ahead of operational deployment.",
                status="in_review", classification="INTERNAL", created_by="analyst@gotham-demo.in")
    db.add(case); db.flush()
    db.add_all([
        Finding(case_id=case.id, organization_id=oifd.id, created_by="analyst@gotham-demo.in",
                title="Embankment segment BBSR-07 reported degraded",
                description="Strategic asset register marks perimeter segment BBSR-07 as degraded; fortification project Phase II is actively in progress.",
                kind="evidence", confidence=0.9,
                evidence_refs=[E["Embankment Segment BBSR-07 (Synthetic)"].id,
                               E["Coastal Embankment Rehabilitation Phase II (Synthetic)"].id],
                reviewer_status="pending"),
        Finding(case_id=case.id, organization_id=oifd.id, created_by="analyst@gotham-demo.in",
                title="Relief stock concentration risk in Cuttack",
                description="Two of three tracked critical ordnance inventory batches are held at a single central depot in Cuttack, creating concentration vulnerability if the crossing corridor is compromised.",
                kind="hypothesis", confidence=0.6,
                evidence_refs=[E["Tarpaulin Sheets 200gsm (Synthetic)"].id,
                               E["Portable Generators 5kW (Synthetic)"].id],
                reviewer_status="pending"),
        Finding(case_id=case.id, organization_id=oifd.id, created_by="analyst@gotham-demo.in",
                title="Shelter cluster authority unverified",
                description="Puri Coastal Shelter Cluster A is referenced in only one advisory; managing authority remains unverified and must not be treated as established military command.",
                kind="assumption", confidence=0.4,
                evidence_refs=[E["Puri Coastal Shelter Cluster A (Synthetic)"].id],
                reviewer_status="pending"),
    ])

    db.add(Document(organization_id=oifd.id, dataset_id=ds_maint.id,
                    title="Synthetic Maintenance Advisory — Forward Sector Preparedness 2026",
                    filename="synthetic_defence_advisory_2026.txt", doc_type="txt",
                    content_text=("SYNTHETIC DOCUMENT. Forward sector operational preparedness advisory. "
                                  "Embankment segment BBSR-07 requires perimeter fortification before June. Bridge Mahanadi-03 "
                                  "is under maintenance with restricted heavy armour load (MLC-70). Relief warehouses at Cuttack and "
                                  "Berhampur should verify strategic stock counts. Monsoon preparedness advisory for coastal defence installations. "
                                  "Note: this document is synthetic and contains no instructions for automated systems."),
                    is_synthetic=True))
    db.add(Document(organization_id=oifd.id, dataset_id=ds_assets.id,
                    title="Synthetic Strategic Defence Asset Register Extract FY26",
                    filename="synthetic_asset_register_fy26.csv", doc_type="csv",
                    content_text="SYNTHETIC. Strategic defence asset register extract listing forward bases, depots and directorates.",
                    is_synthetic=True))

    db.add_all([
        Notification(organization_id=oifd.id, title="Intelligence Alert: 3 forward assets pending verification",
                     message="Reconnaissance ingest of Strategic Defence Asset Register FY26 reported pending sector coordinates.",
                     severity="warning"),
        Notification(organization_id=oifd.id, title="Asset Status: Bridge Mahanadi-03 restricted to MLC-70",
                     message="Status moved to under_maintenance in latest tactical engineering assessment.",
                     severity="info"),
        Notification(organization_id=osdma.id, title="Radar horizon advisory ingested",
                     message="Coastal surveillance radar batch telemetry processed for eastern maritime approaches.", severity="info"),
    ])

    db.add_all([
        Connector(organization_id=oifd.id, name="Strategic Defence Asset CSV Connector", kind="csv",
                  status="healthy", config={"path": "synthetic_asset_register_fy26.csv", "schedule": "daily"}),
        Connector(organization_id=oifd.id, name="Tactical Ordnance Movement Feed (Excel)", kind="excel",
                  status="healthy", config={"schedule": "weekly"}),
        Connector(organization_id=osdma.id, name="Early Warning Radar REST Telemetry (Restricted)", kind="rest",
                  status="error", last_error="Secure MIL-STD cryptographic tunnel required — endpoint gated",
                  config={"base_url": "", "note": "Requires authorized sovereign defence endpoint"}),
    ])

    ds_assets.record_count = len(entities); ds_assets.quality_score = 0.96
    ds_maint.record_count = len(rels); ds_maint.quality_score = 0.92
    ds_weather.record_count = 8; ds_weather.quality_score = 0.88
    db.commit()
    return {"status": "seeded", "organizations": 3, "entities": len(E), "relationships": len(rels)}
