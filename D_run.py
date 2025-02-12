import argparse

import torch
from torchvision import utils
from model import Generator, Discriminator
from tqdm import tqdm
from dataset import Dataset


def generate(args, g_ema, D, device, mean_latent):

    with torch.no_grad():
        g_ema.eval()
        for i in tqdm(range(args.pics)):
            sample_z = torch.randn(args.sample, args.latent, device=device)

            sample, _ = g_ema(
                [sample_z], truncation=args.truncation, truncation_latent=mean_latent
            )
            # import pdb; pdb.set_trace()
            print("Fake images:", torch.sigmoid(D(sample)).mean())
            utils.save_image(
                sample,
                f"sample/{str(i).zfill(6)}.png",
                nrow=1,
                normalize=True,
                range=(-1, 1),
            )


if __name__ == "__main__":
    # device = torch.device('cuda')
    device = torch.device('cpu')
    parser = argparse.ArgumentParser(description="Generate samples from the generator")

    parser.add_argument(
        "--size", type=int, default=256, help="output image size of the generator"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=64,
        help="number of samples to be generated for each image",
    )
    parser.add_argument(
        "--pics", type=int, default=20, help="number of images to be generated"
    )
    parser.add_argument("--truncation", type=float, default=1, help="truncation ratio")
    parser.add_argument(
        "--truncation_mean",
        type=int,
        default=4096,
        help="number of vectors to calculate mean for the truncation",
    )
    parser.add_argument(
        "--ckpt",
        type=str,
        default="stylegan2-ffhq-config-f.pt",
        help="path to the model checkpoint",
    )
    parser.add_argument(
        "--channel_multiplier",
        type=int,
        default=2,
        help="channel multiplier of the generator. config-f = 2, else = 1",
    )

    args = parser.parse_args()

    args.latent = 512
    args.n_mlp = 8

    g_ema = Generator(
        args.size, args.latent, args.n_mlp, channel_multiplier=args.channel_multiplier
    ).to(device)
    discriminator = Discriminator(
        args.size, channel_multiplier=args.channel_multiplier
    ).to(device)

    ckpt = torch.load(args.ckpt, map_location=lambda storage, loc: storage)
    # ckpt = torch.load(args.ckpt, map_location=device)
    dataset = Dataset(path = 'dataset/FFHQ_256')
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=False)
    true_imgs = next(iter(dataloader))
    # import pdb; pdb.set_trace()
    discriminator.load_state_dict(ckpt["d"])
    g_ema.load_state_dict(ckpt["g_ema"], strict=False)

    # import pdb; pdb.set_trace()
    if args.truncation < 1:
        with torch.no_grad():
            mean_latent = g_ema.mean_latent(args.truncation_mean)
    else:
        mean_latent = None
    # import pdb; pdb.set_trace()
    print("True images:", torch.sigmoid(discriminator(true_imgs)).mean())
    generate(args, g_ema, discriminator, device, mean_latent)
