    dest_lang = request.args.get('lang', 'en').lower()
    pil_img = None
    img_byte_arr = None

    try:
        # Check if it's JSON from Arduino (Base64)
        if request.is_json:
            data = request.get_json()
            base64_img_str = data.get('file', None)
            if not base64_img_str:
                return jsonify({"error": "No 'file' key found in JSON payload (Base64 data missing)."}), 400
            
            # Decode Base64 string to bytes
            image_bytes = base64.b64decode(base64_img_str)
            img_byte_arr = BytesIO(image_bytes)
            pil_img = Image.open(img_byte_arr).convert('RGB')
        
        # Check if it's a regular file upload (e.g., from the web form)
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No selected image file."}), 400
            
            # Read the file data into a BytesIO object for re-use (Telegram)
            img_byte_arr = BytesIO(file.read())
            img_byte_arr.seek(0) # Reset pointer
            pil_img = Image.open(img_byte_arr).convert('RGB')
        
        else:
            return jsonify({"error": "Unsupported Media Type or no file provided. Expected JSON (Base64) or multipart/form-data."}), 415

    except Exception as e:
        # Catch errors like corrupted Base64 or non-image data
        return jsonify({"error": f"Failed to process image data: {str(e)}"}), 400
