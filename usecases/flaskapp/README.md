Expected diff output:

```python
diff --git a/usecases/flask/source.py b/usecases/flask/source.py
index 670cc2d..59c0d88 100644
--- a/usecases/flask/source.py
+++ b/usecases/flask/source.py
@@ -1,10 +1,11 @@
+
 from flask import Flask


 def create_app():
     app = Flask(__name__)

-    @app.route("/", methods=["GET", "POST"])
+    @app.route("/", methods=["POST"])
     def hello_world():
         return "<p>Hello, World!</p>"
```
