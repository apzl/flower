import flwr as fl
import hydra
from hydra.core.hydra_config import HydraConfig
from hydra.utils import instantiate, call
from omegaconf import DictConfig, OmegaConf

from fedpac import client, server, utils
from fedpac.dataset import load_datasets
from fedpac.utils import save_results_as_pickle


@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Main function to run federated learning rounds.

    Parameters
    ----------
    cfg : DictConfig
        An omegaconf object that stores the hydra config.
    """

    # print config structured as YAML
    print(OmegaConf.to_yaml(cfg))

    # partition dataset and get dataloaders
    trainloaders, valloaders, testloader = load_datasets(
        config=cfg.dataset_config,
        num_clients=cfg.num_clients,
        batch_size=cfg.batch_size,
    )

    client_fn = call(
        cfg.gen_client_fn,
        num_epochs=cfg.num_epochs,
        trainloaders=trainloaders,
        valloaders=valloaders,
        learning_rate=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
        momentum=cfg.momentum
        )
    # get function that will executed by the strategy's evaluate() method
    # Set server's device
    device = cfg.server_device
    evaluate_fn = server.gen_evaluate_fn(testloader, device=device, model=cfg.model)

    # get a function that will be used to construct the config that the client's
    # fit() method will received
    # def get_on_fit_config():
    #     def fit_config_fn(server_round: int, global_centroid):
    #         # resolve and convert to python dict
    #         fit_config = OmegaConf.to_container(cfg.fit_config, resolve=True)
    #         fit_config["curr_round"] = server_round             # add round info
    #         fit_config.update({"global_centroid":global_centroid, 
    #                             "classifier_head": None
    #                         }) 
    #         return fit_config

    #     return fit_config_fn

    # instantiate strategy according to config. Here we pass other arguments
    # that are only defined at run time.
    strategy = instantiate(
        cfg.strategy,
        evaluate_fn=evaluate_fn
    )

    # Start simulation
    history = fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=cfg.num_clients,
        config=fl.server.ServerConfig(num_rounds=cfg.num_rounds),
        client_resources={
            "num_cpus": cfg.client_resources.num_cpus,
            "num_gpus": cfg.client_resources.num_gpus,
        },
        strategy=strategy,
    )

    # Experiment completed. Now we save the results and
    # generate plots using the `history`
    print("................")
    # print(history)
    # Hydra automatically creates an output directory
    # Let's retrieve it and save some results there
    save_path = HydraConfig.get().runtime.output_dir

    # save results as a Python pickle using a file_path
    # the directory created by Hydra for each run
    # save_results_as_pickle(history, file_path=save_path, extra_results={})

    # plot results and include them in the readme
    strategy_name = strategy.__class__.__name__
    file_suffix: str = (
        f"_{strategy_name}"
        f"{'_iid' if cfg.dataset_config.iid else ''}"
        f"{'_balanced' if cfg.dataset_config.balance else ''}"
        f"_C={cfg.num_clients}"
        f"_B={cfg.batch_size}"
        f"_E={cfg.num_epochs}"
        f"_R={cfg.num_rounds}"
        f"_lam={cfg.lamda}"
    )
    utils.plot_metric_from_history(
        history,
        save_path,
        (file_suffix),
    )


if __name__ == "__main__":
    main()
