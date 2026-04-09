"""
sample_diffs.py
---------------
A collection of sample diffs for testing and demo purposes.
Use these to evaluate the reviewer without needing a real GitHub PR.
"""

SAMPLES = {
    "SQL Injection + Weak Auth": """\
--- a/auth/login.py
+++ b/auth/login.py
@@ -5,12 +5,18 @@
 import time
+import hashlib
 from db import get_connection

 def login(username, password):
-    db = get_connection()
-    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
-    result = db.execute(query)
+    db = get_connection()
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    result = db.execute(query).fetchone()
     if result:
-        return True
+        token = hashlib.md5((username + str(time.time())).encode()).hexdigest()
+        return {"status": "ok", "token": token, "user_id": result["id"]}
+    return {"status": "error", "message": "Invalid credentials"}
""",

    "Memory Leak + Race Condition": """\
--- a/services/cache.py
+++ b/services/cache.py
@@ -1,20 +1,28 @@
+import threading
 from collections import defaultdict

 class Cache:
     def __init__(self):
         self._store = defaultdict(list)
+        self._hits = 0

     def set(self, key, value, ttl=None):
-        self._store[key] = value
+        self._store[key].append(value)  # append instead of overwrite

     def get(self, key):
+        self._hits += 1  # not thread-safe
         if key in self._store:
-            return self._store[key]
+            return self._store[key][-1]
         return None

+    def clear(self):
+        # Only clears values, keys remain
+        for key in self._store:
+            self._store[key] = []
""",

    "Clean Refactor (positive example)": """\
--- a/utils/parser.py
+++ b/utils/parser.py
@@ -10,20 +10,25 @@
-def parse_user_input(raw):
-    parts = raw.split(",")
-    name = parts[0]
-    age = parts[1]
-    email = parts[2]
-    return name, age, email
+from dataclasses import dataclass
+from typing import Optional
+
+@dataclass
+class UserInput:
+    name: str
+    age: int
+    email: str
+
+def parse_user_input(raw: str) -> Optional[UserInput]:
+    \"\"\"Parse a comma-separated user record into a typed dataclass.\"\"\"
+    try:
+        name, age_str, email = raw.strip().split(",", maxsplit=2)
+        return UserInput(name=name.strip(), age=int(age_str.strip()), email=email.strip())
+    except (ValueError, AttributeError):
+        return None
""",

    "N+1 Query Problem": """\
--- a/api/orders.py
+++ b/api/orders.py
@@ -8,14 +8,20 @@
 from models import Order, User
 from flask import jsonify

 @app.route("/orders")
 def get_orders():
-    orders = Order.query.all()
+    orders = Order.query.filter_by(status="active").all()
     result = []
     for order in orders:
-        result.append({"id": order.id, "total": order.total})
+        # Fetch user for each order individually
+        user = User.query.get(order.user_id)
+        result.append({
+            "id": order.id,
+            "total": order.total,
+            "user_email": user.email,
+            "user_name": user.name,
+        })
     return jsonify(result)
""",
}


if __name__ == "__main__":
    # Quick CLI test — run: python sample_diffs.py
    from reviewer import review_diff

    print("Available sample diffs:")
    for i, name in enumerate(SAMPLES, 1):
        print(f"  {i}. {name}")

    choice = int(input("\nPick a sample (number): ")) - 1
    name = list(SAMPLES.keys())[choice]
    diff = SAMPLES[name]

    print(f"\n📋 Reviewing: {name}\n{'='*60}")
    review = review_diff(diff)
    print(review)