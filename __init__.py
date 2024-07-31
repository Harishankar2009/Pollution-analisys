from flask import Flask, jsonify, request
from .map_segmentation import map_segmentation

app = Flask(__name__)

@app.route("/location/<place>")
def for_particular_place(place):
    area, trees = map_segmentation(place)
    return jsonify({"total_acres_of_land": area, "total_number_of_trees": trees})

@app.route("/coordinates/")
def for_particular_coordinates():
    ullat, ullon = float(request.args.get('ullat')), float(request.args.get('ullon'))
    lrlat, lrlon = float(request.args.get('Irlat')), float(request.args.get('Irlon'))
    area, trees = map_segmentation(ullat, ullon, lrlat, lrlon)
    return jsonify({"total_acres_of_land": area, "total_number_of_trees": trees})

if __name__ == '__main__':
    app.run(debug=True)
