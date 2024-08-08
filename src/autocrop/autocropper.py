from transformers import YolosImageProcessor, YolosForObjectDetection
from PIL import Image, ImageOps
import torch
import os
import sys
import json
from autocrop.importance_weights import importance_weights
from mosaic_util.image_utility import image_smart_open


script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.append(project_dir)


def obj_center(box, label):
    # averaging the anchor points of the box to get the center
    offset = 0.25 if label == "1" else 0
    return torch.tensor([(box[2] + box[0]) * 0.5, ((box[3] + box[1]) * 0.5 - (box[3] - box[1]) * offset)])


def box_dim(box):
    # averaging the anchor points of the box to get the center
    return [(box[2] - box[0]).item(), (box[3] - box[1]).item()]


def main(directory):
    print("cropping")
    if torch.cuda.is_available():
        device = torch.device("cuda")

    model = YolosForObjectDetection.from_pretrained(os.path.join(project_dir, "models", "yolos_model")).to(device)
    image_processor = YolosImageProcessor.from_pretrained(os.path.join(project_dir, "models", "yolos_image_processor"))

    files = os.listdir(directory)
    total = len(files)
    count = 1

    crops = {}
    for f in files:
        if f.endswith((".PNG", ".png", ".jpg")):
            print(f"{count} of {total}: {f}")
            with image_smart_open(os.path.join(directory, f)) as image:
                s = image.size
                # patch for weird issue where square image break the model
                if s[0] == s[1]:
                    image = ImageOps.expand(image, border=(0, 1), fill="black")
                # print(image.size)
                inputs = image_processor(images=image, return_tensors="pt").to(device)
                # print(inputs["pixel_values"].shape)
            outputs = model(**inputs)

            target_sizes = torch.tensor([image.size[::-1]])
            # print(target_sizes)
            results = image_processor.post_process_object_detection(outputs, threshold=0, target_sizes=target_sizes)[0]
            _, top_indices = torch.topk(results["scores"], 10)

            for _, label, box in zip(
                results["scores"][top_indices], results["labels"][top_indices], results["boxes"][top_indices]
            ):
                box = [round(i, 2) for i in box.tolist()]
                # print(
                #     f"Detected {model.config.id2label[label.item()]} with confidence " f"{round(score.item(), 3)} at location {box}"
                # )

            # New bounding box using weighted importance of top 5 objects
            total_weight = 0
            total_posn = torch.zeros(2)
            w, h = image.size
            area = w * h
            for i in top_indices:
                box = results["boxes"][i]
                label = str(results["labels"][i].item())
                # print("box", box)
                c = obj_center(box, label)
                # print("center", c)
                boxw, boxh = box_dim(box)
                importance = importance_weights[label] * results["scores"][i].item() ** 6 * (boxw * boxh / area)
                # print("importance", importance)
                total_posn += c * importance
                # print("total_posn", total_posn)
                total_weight += importance
            posn = total_posn / total_weight

            # print("w, h: ", (w, h))
            box_size = min(w, h)
            xl = min(max(posn[0].item() - box_size / 2, 0), w - box_size)
            yl = min(max(posn[1].item() - box_size / 2, 0), h - box_size)
            bounding_box = (xl, yl, xl + box_size, yl + box_size)
            crops[f] = bounding_box

            # Cleanup
            del inputs, outputs, results  # Delete any large variables explicitly
            torch.cuda.empty_cache()  # Free up unused memory
        count += 1
    with open(os.path.join(directory, "lib.crop"), "w") as json_file:
        json.dump(crops, json_file)
    print(os.path.join(directory, "lib.crop"))
    print("done cropping")
