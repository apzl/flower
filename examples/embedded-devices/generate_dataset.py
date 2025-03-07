import argparse
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import IidPartitioner


DATASET_DIRECTORY = "datasets"


def save_dataset_to_disk(num_partitions: int):
    """This function downloads the Fashion-MNIST dataset and generates N partitions.

    Each will be saved into the DATASET_DIRECTORY.
    """
    partitioner = IidPartitioner(num_partitions=num_partitions)
    fds = FederatedDataset(
        dataset="zalando-datasets/fashion_mnist",
        partitioners={"train": partitioner},
    )

    for partition_id in range(num_partitions):
        partition = fds.load_partition(partition_id)
        partition_train_test = partition.train_test_split(test_size=0.2, seed=42)
        file_path = f"./{DATASET_DIRECTORY}/fashionmnist_part_{partition_id + 1}"
        partition_train_test.save_to_disk(file_path)
        print(f"Written: {file_path}")


if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser(
        description="Save Fashion-MNIST dataset partitions to disk"
    )

    # Add an optional positional argument for number of partitions
    parser.add_argument(
        "--num-supernodes",
        type=int,
        nargs="?",
        default=2,
        help="Number of partitions to create (default: 2)",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Call the function with the provided argument
    save_dataset_to_disk(args.num_supernodes)
