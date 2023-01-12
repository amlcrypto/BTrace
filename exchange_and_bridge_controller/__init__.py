import exchange_and_bridge_controller.everscale as ev

class Controller ():
    @classmethod
    async def check_wallet (cls, wallet: str, blockhain: str) -> list:
        #run a check wallet on blockchain
        if (blockhain == 'Everscale Mainnet'):
            return await cls._check_ever(wallet)
        elif (blockhain == 'Solana'):
            return cls._check_solana()
        elif (blockhain == 'Tron'):
            return cls._check_tron()
        return True

    async def _check_ever(wallet: str) -> list:
        return await ev.check(wallet)

    def _check_tron(wallet: str):
        pass

    def _check_solana(wallet: str):
        pass