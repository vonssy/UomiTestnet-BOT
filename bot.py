from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from eth_abi.abi import encode
from eth_utils import to_bytes
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from datetime import datetime
from colorama import *
import asyncio, random, time, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class UOMI:
    def __init__(self) -> None:
        self.RPC_URL = "https://finney.uomi.ai/"
        self.WUOMI_CONTRACT_ADDRESS = "0x5FCa78E132dF589c1c799F906dC867124a2567b2"
        self.USDC_CONTRACT_ADDRESS = "0xAA9C4829415BCe70c434b7349b628017C59EC2b1"
        self.SYN_CONTRACT_ADDRESS = "0x2922B2Ca5EB6b02fc5E1EBE57Fc1972eBB99F7e0"
        self.SIM_CONTRACT_ADDRESS = "0x04B03e3859A25040E373cC9E8806d79596D70686"
        self.PERMIT_ROUTER_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
        self.EXECUTE_ROUTER_ADDRESS = "0x197EEAd5Fe3DB82c4Cd55C5752Bc87AEdE11f230"
        self.POSITION_ROUTER_ADDRESS = "0x906515Dc7c32ab887C8B8Dce6463ac3a7816Af38"
        self.QUOTER_ROUTER_ADDRESS = "0xCcB2B2F8395e4462d28703469F84c95293845332"
        self.ERC20_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]},
            {"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]},
            {"type":"function","name":"deposit","stateMutability":"payable","inputs":[],"outputs":[]},
            {"type":"function","name":"withdraw","stateMutability":"nonpayable","inputs":[{"name":"wad","type":"uint256"}],"outputs":[]}
        ]''')
        self.UOMI_CONTRACT_ABI = [
            {
                "type": "function",
                "name": "quoteExactInput",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "bytes", "name": "path", "type": "bytes" },
                    { "internalType": "uint256", "name": "amountIn", "type": "uint256" }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "amountOut", "type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "execute",
                "stateMutability": "payable",
                "inputs": [
                    { "internalType": "bytes", "name": "commands", "type": "bytes" },
                    { "internalType": "bytes[]", "name": "inputs", "type": "bytes[]" },
                    { "internalType": "uint256", "name": "deadline", "type": "uint256" }
                ],
                "outputs": []
            },
            {
                "type": "function",
                "name": "multicall",
                "stateMutability": "payable",
                "inputs": [
                    { "internalType": "bytes[]", "name": "data", "type": "bytes[]" }
                ],
                "outputs": [
                    { "internalType": "bytes[]", "name": "results", "type": "bytes[]" }
                ]
            },
            {
                "type": "function",
                "name": "mint",
                "stateMutability": "nonpayable",
                "inputs": [
                    {
                        "type": "tuple",
                        "name": "params",
                        "internalType": "struct INonfungiblePositionManager.MintParams",
                        "components": [
                            { "internalType": "address", "name": "token0", "type": "address" },
                            { "internalType": "address", "name": "token1", "type": "address" },
                            { "internalType": "uint24", "name": "fee", "type": "uint24" },
                            { "internalType": "int24", "name": "tickLower", "type": "int24" },
                            { "internalType": "int24", "name": "tickUpper", "type": "int24" },
                            { "internalType": "uint256", "name": "amount0Desired", "type": "uint256" },
                            { "internalType": "uint256", "name": "amount1Desired", "type": "uint256" },
                            { "internalType": "uint256", "name": "amount0Min", "type": "uint256" },
                            { "internalType": "uint256", "name": "amount1Min", "type": "uint256" },
                            { "internalType": "address", "name": "recipient", "type": "address" },
                            { "internalType": "uint256", "name": "deadline", "type": "uint256" }
                        ]
                    }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "tokenId", "type": "uint256" },
                    { "internalType": "uint128", "name": "liquidity", "type": "uint128" },
                    { "internalType": "uint256", "name": "amount0", "type": "uint256" },
                    { "internalType": "uint256", "name": "amount1", "type": "uint256" }
                ]
            }
        ]
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.used_nonce = {}
        self.wrap_option = 0
        self.wrap_amount = 0
        self.swap_count = 0
        self.min_swap_amount = 0
        self.max_swap_amount = 0
        self.liquidity_count = 0
        self.uomi_amount = 0
        self.wuomi_amount = 0
        self.syn_amount = 0
        self.sim_amount = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Uomi Testnet{Fore.BLUE + Style.BRIGHT} Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: bool):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Address Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}                  "
            )
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def generate_swap_option(self):
        swap_options = [
            ("UOMI to USDC", self.WUOMI_CONTRACT_ADDRESS, self.USDC_CONTRACT_ADDRESS),
            ("UOMI to SYN", self.WUOMI_CONTRACT_ADDRESS, self.SYN_CONTRACT_ADDRESS),
            ("UOMI to SIM", self.WUOMI_CONTRACT_ADDRESS, self.SIM_CONTRACT_ADDRESS)
        ]

        swap_option, from_token, to_token = random.choice(swap_options)

        amount_in = round(random.uniform(self.min_swap_amount, self.max_swap_amount), 6)

        return swap_option, from_token, to_token, amount_in

    def generate_liquidity_option(self):
        swap_options = [
            # ("native", "USDC", "UOMI", self.USDC_CONTRACT_ADDRESS, self.WUOMI_CONTRACT_ADDRESS, self.usdc_amount),
            ("native", "SYN", "UOMI", self.SYN_CONTRACT_ADDRESS, self.WUOMI_CONTRACT_ADDRESS, self.uomi_amount),
            ("native", "SIM", "UOMI", self.SIM_CONTRACT_ADDRESS, self.WUOMI_CONTRACT_ADDRESS, self.uomi_amount),
            ("erc20", "WUOMI", "USDC", self.WUOMI_CONTRACT_ADDRESS, self.USDC_CONTRACT_ADDRESS, self.wuomi_amount),
            ("erc20", "SYN", "WUOMI", self.SYN_CONTRACT_ADDRESS, self.WUOMI_CONTRACT_ADDRESS, self.syn_amount),
            ("erc20", "SYN", "USDC", self.SYN_CONTRACT_ADDRESS, self.USDC_CONTRACT_ADDRESS, self.syn_amount),
            ("erc20", "SIM", "WUOMI", self.SIM_CONTRACT_ADDRESS, self.WUOMI_CONTRACT_ADDRESS, self.sim_amount),
            ("erc20", "SIM", "USDC", self.SIM_CONTRACT_ADDRESS, self.USDC_CONTRACT_ADDRESS, self.sim_amount),
            ("erc20", "SIM", "SYN", self.SIM_CONTRACT_ADDRESS, self.SYN_CONTRACT_ADDRESS, self.sim_amount)
        ]

        token_type, ticker0, ticker1, token0, token1, amount0 = random.choice(swap_options)

        liquidity_option = f"{ticker0}/{ticker1}"

        amount0_desired = int(amount0 * (10 ** 18))

        return liquidity_option, token_type, ticker0, ticker1, token0, token1, amount0_desired
        
    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
            
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Send TX Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Wait for Receipt Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
        
    async def get_token_balance(self, address: str, contract_address: str, use_proxy: bool, retries=5):
        for attempt in range(retries):
            try:
                web3 = await self.get_web3_with_check(address, use_proxy)

                if contract_address == "UOMI":
                    balance = web3.eth.get_balance(address)
                    decimals = 18
                else:
                    token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
                    balance = token_contract.functions.balanceOf(address).call()
                    decimals = token_contract.functions.decimals().call()

                token_balance = balance / (10 ** decimals)

                return token_balance
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                return None
        
    async def perform_wrapped(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            contract_address = web3.to_checksum_address(self.WUOMI_CONTRACT_ADDRESS)
            token_contract = web3.eth.contract(address=contract_address, abi=self.ERC20_CONTRACT_ABI)

            amount_to_wei = web3.to_wei(self.wrap_amount, "ether")
            wrap_data = token_contract.functions.deposit()
            estimated_gas = wrap_data.estimate_gas({"from":address, "value":amount_to_wei})

            max_priority_fee = web3.to_wei(28.54, "gwei")
            max_fee = max_priority_fee

            wrap_tx = wrap_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, wrap_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_unwrapped(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            contract_address = web3.to_checksum_address(self.WUOMI_CONTRACT_ADDRESS)
            token_contract = web3.eth.contract(address=contract_address, abi=self.ERC20_CONTRACT_ABI)

            amount_to_wei = web3.to_wei(self.wrap_amount, "ether")
            unwrap_data = token_contract.functions.withdraw(amount_to_wei)
            estimated_gas = unwrap_data.estimate_gas({"from":address})

            max_priority_fee = web3.to_wei(28.54, "gwei")
            max_fee = max_priority_fee

            unwrap_tx = unwrap_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, unwrap_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def get_amount_out_min(self, address: str, path: str, amount_in_wei: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            contract = web3.eth.contract(address=web3.to_checksum_address(self.QUOTER_ROUTER_ADDRESS), abi=self.UOMI_CONTRACT_ABI)

            amount_out = contract.functions.quoteExactInput(path, amount_in_wei).call()
            
            return amount_out
        except Exception as e:
            return None
        
    async def approving_token(self, account: str, address: str, router_address: str, asset_address: str, amount_to_wei: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            spender = web3.to_checksum_address(router_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(asset_address), abi=self.ERC20_CONTRACT_ABI)

            allowance = token_contract.functions.allowance(address, spender).call()
            if allowance < amount_to_wei:
                approve_data = token_contract.functions.approve(spender, 2**256 - 1)
                estimated_gas = approve_data.estimate_gas({"from": address})

                max_priority_fee = web3.to_wei(28.54, "gwei")
                max_fee = max_priority_fee

                approve_tx = approve_data.build_transaction({
                    "from": address,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": self.used_nonce[address],
                    "chainId": web3.eth.chain_id,
                })

                tx_hash = await self.send_raw_transaction_with_retries(account, web3, approve_tx)
                receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
                block_number = receipt.blockNumber
                self.used_nonce[address] += 1

                explorer = f"https://testnet.pharosscan.xyz/tx/{tx_hash}"
                
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Approve  :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
                )
                await self.print_timer()

            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")
        
    async def perform_swap(self, account: str, address: str, from_token: str, to_token: str, amount_in: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            amount_in_wei = web3.to_wei(amount_in, "ether")

            commands = to_bytes(hexstr="0x0b00")

            wrap_eth = encode(
                ['address', 'uint256'],
                [
                    '0x0000000000000000000000000000000000000002',
                    amount_in_wei
                ]
            )

            path = bytes.fromhex(from_token[2:]) + (3000).to_bytes(3, "big") + bytes.fromhex(to_token[2:])

            amount_out_wei = await self.get_amount_out_min(address, path, amount_in_wei, use_proxy)
            if not amount_out_wei:
                raise Exception("GET Amount Out Min Failed")
            
            amount_out_min_wei = (amount_out_wei * (10000 - 50)) // 10000

            v3_swap_exact_in = encode(
                ['address', 'uint256', 'uint256', 'bytes', 'bool'],
                [
                    '0x0000000000000000000000000000000000000001',
                    amount_in_wei,
                    amount_out_min_wei,
                    path,
                    False
                ]
            )

            inputs = [wrap_eth, v3_swap_exact_in]

            deadline = int(time.time()) + 600

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.EXECUTE_ROUTER_ADDRESS), abi=self.UOMI_CONTRACT_ABI)

            swap_data = token_contract.functions.execute(commands, inputs, deadline)

            estimated_gas = swap_data.estimate_gas({"from": address, "value":amount_in_wei})

            max_priority_fee = web3.to_wei(28.54, "gwei")
            max_fee = max_priority_fee

            swap_tx = swap_data.build_transaction({
                "from": address,
                "value": amount_in_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, swap_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    def generate_liquidity_calldata(self, address: str, token_type: str, token0: str, token1: str, amount0_desired: int, amount1_desired: int):
        try:
            amount0_min = (amount0_desired * (10000 - 100)) // 10000
            amount1_min = (amount1_desired * (10000 - 100)) // 10000
            deadline = int(time.time()) + 600

            if token_type == "native":
                prefix = bytes.fromhex("88316456")
                mint_params = encode(
                    [
                        'address', 'address', 'uint24', 'int24', 'int24', 'uint256', 
                        'uint256', 'uint256', 'uint256', 'address', 'uint256'
                    ],
                    [
                        token0, token1, 3000, -887220, 887220, amount0_desired,
                        amount1_desired, amount0_min, amount1_min, address, deadline
                    ]
                )

                mint =  prefix + mint_params
                refund_eth = bytes.fromhex("12210e8a")

                calldata = [mint, refund_eth]

            elif token_type == "erc20":
                calldata = (
                    token0, token1, 3000, -887220, 887220, amount0_desired, 
                    amount1_desired, amount0_min, amount1_min, address, deadline
                )

            return calldata
        except Exception as e:
            raise Exception(f"Generate Calldata Failed: {str(e)}")
        
    async def perform_liquidity(self, account: str, address: str, token_type: str, token0: str, token1: str, amount0_desired: int, amount1_desired: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            await self.approving_token(account, address, self.POSITION_ROUTER_ADDRESS, token0, amount0_desired, use_proxy)

            if token_type == "erc20":
                await self.approving_token(account, address, self.POSITION_ROUTER_ADDRESS, token1, amount1_desired, use_proxy)
            

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.POSITION_ROUTER_ADDRESS), abi=self.UOMI_CONTRACT_ABI)

            calldata = self.generate_liquidity_calldata(address, token_type, token0, token1, amount0_desired, amount1_desired)

            max_priority_fee = web3.to_wei(28.54, "gwei")
            max_fee = max_priority_fee

            if token_type == "native":
                liquidity_data = token_contract.functions.multicall(calldata)
                estimated_gas = liquidity_data.estimate_gas({"from": address, "value":amount1_desired})
                liquidity_tx = liquidity_data.build_transaction({
                    "from": address,
                    "value": amount1_desired,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": self.used_nonce[address],
                    "chainId": web3.eth.chain_id
                })

            elif token_type == "erc20":
                liquidity_data = token_contract.functions.mint(calldata)
                estimated_gas = liquidity_data.estimate_gas({"from": address})
                liquidity_tx = liquidity_data.build_transaction({
                    "from": address,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": self.used_nonce[address],
                    "chainId": web3.eth.chain_id
                })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, liquidity_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    def print_wrap_question(self):
        while True:
            try:
                wrap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter UOMI Amount -> {Style.RESET_ALL}").strip())
                if wrap_amount > 0:
                    self.wrap_amount = wrap_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}UOMI Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
    
    def print_unwrap_question(self):
        while True:
            try:
                wrap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter WUOMI Amount -> {Style.RESET_ALL}").strip())
                if wrap_amount > 0:
                    self.wrap_amount = wrap_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}WUOMI Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

    def print_wrap_or_unwarp_option(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Wrap UOMI{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Unwrap WUOMI{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Skipped{Style.RESET_ALL}")
                wrap_option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if wrap_option in [1, 2, 3]:
                    wrap_type = (
                        "Wrap UOMI" if wrap_option == 1 else 
                        "Unwrap WUOMI" if wrap_option == 2 else 
                        "Skipped"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{wrap_type} Selected.{Style.RESET_ALL}")
                    self.wrap_option = wrap_option

                    if self.wrap_option == 1:
                        self.print_wrap_question()
                    elif self.wrap_option == 2:
                        self.print_unwrap_question()

                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

    def print_swap_question(self):
        while True:
            try:
                swap_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Swap Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if swap_count > 0:
                    self.swap_count = swap_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Swap Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                min_swap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Min UOMI Amount -> {Style.RESET_ALL}").strip())
                if min_swap_amount > 0:
                    self.min_swap_amount = min_swap_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min UOMI Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

        while True:
            try:
                max_swap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Max UOMI Amount -> {Style.RESET_ALL}").strip())
                if max_swap_amount >= min_swap_amount:
                    self.max_swap_amount = max_swap_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Max UOMI Amount must be >= Min UOMI.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
    
    def print_liquidity_question(self):
        while True:
            try:
                liquidity_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Add Liquidity Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if liquidity_count > 0:
                    self.liquidity_count = liquidity_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Add Liquidity Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                uomi_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter UOMI Amount -> {Style.RESET_ALL}").strip())
                if uomi_amount > 0:
                    self.uomi_amount = uomi_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}UOMI Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")
        
        while True:
            try:
                wuomi_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter WUOMI Amount -> {Style.RESET_ALL}").strip())
                if wuomi_amount > 0:
                    self.wuomi_amount = wuomi_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}WUOMI Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

        while True:
            try:
                syn_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter SYN Amount -> {Style.RESET_ALL}").strip())
                if syn_amount > 0:
                    self.syn_amount = syn_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}SYN Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

        while True:
            try:
                sim_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter SIM Amount -> {Style.RESET_ALL}").strip())
                if sim_amount > 0:
                    self.sim_amount = sim_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}SIM Amount must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay For Each Tx -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay For Each Tx -> {Style.RESET_ALL}").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Max Delay must be >= Min Delay.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
         
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Wrap UOMI{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Unwrap WUOMI{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Random Swap{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}4. Add Liquidity{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}5. Run All Features{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3/4/5] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3, 4, 5]:
                    option_type = (
                        "Wrap UOMI" if option == 1 else 
                        "Unwrap WUOMI" if option == 2 else 
                        "Random Swap" if option == 3 else
                        "Add Liquidity" if option == 4 else
                        "Run All Features"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{option_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, 3, 4, or 5.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, 4, or 5).{Style.RESET_ALL}")

        if option == 1:
            self.print_wrap_question()
            self.print_delay_question()

        elif option == 2:
            self.print_unwrap_question()
            self.print_delay_question()

        elif option == 3:
            self.print_swap_question()
            self.print_delay_question()

        elif option == 4:
            self.print_liquidity_question()
            self.print_delay_question()

        elif option == 5:
            self.print_wrap_or_unwarp_option()
            self.print_swap_question()
            self.print_liquidity_question()
            self.print_delay_question()

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Free Proxyscrape Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Free Proxyscrape" if choose == 1 else 
                        "With Private" if choose == 2 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        rotate = False
        if choose in [1, 2]:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return option, choose, rotate
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    continue

                return False
            
            return True
        
    async def process_perform_wrapped(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_wrapped(account, address, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.uomi.ai/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_unwrapped(self, account: str, address: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_unwrapped(account, address, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.uomi.ai/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_swap(self, account: str, address: str, from_token: str, to_token: str, amount_in: float, use_proxy: bool):
        tx_hash, block_number = await self.perform_swap(account, address, from_token, to_token, amount_in, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.uomi.ai/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_liquidity(self, account: str, address: str, token_type: str, token0: str, token1: str, amount0_desired: int, amount1_desired: int, use_proxy: bool):
        tx_hash, block_number = await self.perform_liquidity(account, address, token_type, token0, token1, amount0_desired, amount1_desired, use_proxy)
        if tx_hash and block_number:
            explorer = f"https://explorer.uomi.ai/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_option_1(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Wrapped   :{Style.RESET_ALL}                      ")

        balance = await self.get_token_balance(address, "UOMI", use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} UOMI {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.wrap_amount} UOMI {Style.RESET_ALL}"
        )

        if not balance or balance <=  self.wrap_amount:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient UOMI Token Balance {Style.RESET_ALL}"
            )
            return
        
        await self.process_perform_wrapped(account, address, use_proxy)

    async def process_option_2(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Unwrapped :{Style.RESET_ALL}                      ")

        balance = await self.get_token_balance(address, self.WUOMI_CONTRACT_ADDRESS, use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} WUOMI {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.wrap_amount} WUOMI {Style.RESET_ALL}"
        )

        if not balance or balance <=  self.wrap_amount:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient WUOMI Token Balance {Style.RESET_ALL}"
            )
            return
        
        await self.process_perform_unwrapped(account, address, use_proxy)

    async def process_option_3(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Swap      :{Style.RESET_ALL}                      ")
        for i in range(self.swap_count):
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT}Swap{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} / {self.swap_count} {Style.RESET_ALL}                           "
            )

            swap_option, from_token, to_token, amount_in = self.generate_swap_option()

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Option   :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {swap_option} {Style.RESET_ALL}"
            )

            balance = await self.get_token_balance(address, "UOMI", use_proxy)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} UOMI {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {amount_in} UOMI {Style.RESET_ALL}"
            )

            if not balance or balance <=  amount_in:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient UOMI Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_swap(account, address, from_token, to_token, amount_in, use_proxy)
            await self.print_timer()

    async def process_option_4(self, account: str, address: str, use_proxy):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Liquidity :{Style.RESET_ALL}                      ")
        for i in range(self.liquidity_count):
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT}Liquidity{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} / {self.liquidity_count} {Style.RESET_ALL}                           "
            )

            liquidity_option, token_type, ticker0, ticker1, token0, token1, amount0_desired = self.generate_liquidity_option()

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Option   :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {liquidity_option} {Style.RESET_ALL}"
            )

            balance0 = await self.get_token_balance(address, token0, use_proxy)

            if token_type == "native":
                balance1 = await self.get_token_balance(address, "UOMI", use_proxy)

            elif token_type == "erc20":
                balance1 = await self.get_token_balance(address, token1, use_proxy)

            self.log(f"{Fore.CYAN+Style.BRIGHT}   Balance  :{Style.RESET_ALL}")
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT}      ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{balance0} {ticker0}{Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT}      ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{balance1} {ticker1}{Style.RESET_ALL}"
            )

            path = bytes.fromhex(token0[2:]) + (3000).to_bytes(3, "big") + bytes.fromhex(token1[2:])
            amount1_desired = await self.get_amount_out_min(address, path, amount0_desired, use_proxy)
            if not amount0_desired:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Fetch {token0} per {token1} Current Price Failed {Style.RESET_ALL}"
                )
                continue

            amount0 = amount0_desired / (10 ** 18)
            amount1 = amount1_desired / (10 ** 18)

            self.log(f"{Fore.CYAN+Style.BRIGHT}   Amount   :{Style.RESET_ALL}")
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT}      ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{amount0} {ticker0}{Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT}      ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{amount1} {ticker1}{Style.RESET_ALL}"
            )

            if not balance0 or balance0 <=  amount0:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker0} Token Balance {Style.RESET_ALL}"
                )
                continue
            
            if not balance1 or balance1 <=  amount1:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker1} Token Balance {Style.RESET_ALL}"
                )
                continue
            
            await self.process_perform_liquidity(account, address, token_type, token0, token1, amount0_desired, amount1_desired, use_proxy)
            await self.print_timer()

    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            try:
                web3 = await self.get_web3_with_check(address, use_proxy)
                if not web3: return
                
                self.used_nonce[address] = web3.eth.get_transaction_count(address, "pending")

            except Exception as e:
                return self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
            
            if option == 1:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Wrap UOMI {Style.RESET_ALL}"
                )
                await self.process_option_1(account, address, use_proxy)

            elif option == 2:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Unwrap WUOMI {Style.RESET_ALL}"
                )
                await self.process_option_2(account, address, use_proxy)

            elif option == 3:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Random Swap {Style.RESET_ALL}"
                )
                await self.process_option_3(account, address, use_proxy)

            elif option == 4:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Add Liquidity {Style.RESET_ALL}"
                )
                await self.process_option_4(account, address, use_proxy)

            elif option == 5:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Run All Features {Style.RESET_ALL}"
                )

                if self.wrap_option == 1:
                    await self.process_option_1(account, address, use_proxy)
                elif self.wrap_option == 2:
                    await self.process_option_2(account, address, use_proxy)

                await asyncio.sleep(5)

                await self.process_option_3(account, address, use_proxy)
                await asyncio.sleep(5)

                await self.process_option_4(account, address, use_proxy)
                await asyncio.sleep(5)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            option, use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        await self.process_accounts(account, address, option, use_proxy_choice, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 1 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = UOMI()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Uomi Testnet - BOT{Style.RESET_ALL}                                       "                              
        )