from mcp_persor import BVHparser
from glob import glob
import pandas as pd
import json
import re
from os import path, makedirs

bvh_files = glob("**/*.bvh") + glob("**/*.BVH")
for bvh_file in bvh_files:
    print(f"Processing {bvh_file}")
    dir = path.dirname(bvh_file)
    label_file = path.join(dir, "label.csv")

    if not path.exists(label_file):
        print(f"Label file not found: {label_file}")
        continue

    label_define_file = glob(f"{dir}/*.jsonc")[0]
    with open(label_define_file) as f:
        text = f.read()
        re_text = re.sub(r"/\*[\s\S]*?\*/|//[^\"\]\,\[]*\n", "\n", text)
        labels = json.loads(re_text)["labels"]

    bvhp = BVHparser(bvh_file)
    motion_df = bvhp.get_motion_df()
    label_df = pd.read_csv(label_file, names=["label"])

    df = pd.concat([motion_df, label_df], axis=1)

    df["group"] = (df["label"] != df["label"].shift()).cumsum()
    result = [group for _, group in df.groupby(["label", "group"])]
    label_count_map = {label: 1 for label in labels + ["その他"]}

    for group in result:
        label_index = int(group["label"].iloc[0])
        label = labels[label_index] if label_index < len(labels) else "その他"
        label_count = label_count_map[label]

        label_count_map[label] += 1

        group.drop(columns=["group"], inplace=True)
        output_dir = f"data/{dir}"
        output_file = f"{label_index}_{label}-{label_count}.csv"

        if not path.exists(output_dir):
            print(f"Creating directory: {output_dir}")
            makedirs(output_dir)

        group.to_csv(path.join(output_dir, output_file), index=False)