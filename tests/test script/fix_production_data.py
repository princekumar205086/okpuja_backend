#!/usr/bin/env python
"""
Production Data Fix Script
Fix package-service relationships in production
"""

# Run this in your production Django shell:
# python manage.py shell

from puja.models import PujaService, PujaPackage

# Get the services and packages
ganesh_service = PujaService.objects.get(id=8)  # Ganesh Puja
packages = PujaPackage.objects.all()

print("Current package-service relationships:")
for pkg in packages:
    print(f"Package {pkg.id} ({pkg.name}) - Service: {pkg.service}")

print("\nFixing package-service relationships...")

# Fix the relationships - assign packages to Ganesh Puja service
for pkg in packages:
    if not pkg.service:  # If no service assigned
        pkg.service = ganesh_service
        pkg.save()
        print(f"✅ Assigned Package {pkg.id} to Service {ganesh_service.id} ({ganesh_service.title})")

print("\nUpdated package-service relationships:")
for pkg in PujaPackage.objects.all():
    print(f"Package {pkg.id} ({pkg.name}) - Service: {pkg.service}")

print("\n🎉 Package-service relationships fixed!")
print("Now test the cart creation again.")
