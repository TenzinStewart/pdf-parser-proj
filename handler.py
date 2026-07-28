import parser as psr
""" Dashboard"""
run_WCC:bool = False
run_NFCU:bool = False



""" WCC PAYCHECK HANDLING """
if run_WCC:
    # Areas of Interest for Analysis
    directory_stubs = ['advice_num',
                    'pay_begin_date',
                    'pay_end_date',
                    'pay_rate',
                    'hours',
                    'net_pay']
    # All WCC_Paycheck Data (2025 - 2026)
    WCC_stubs = psr.organize(df=psr.process_WCC_Paycheck("data/WCC_paychecks"),
                get_cols=directory_stubs,
                sort_col="advice_num",
                show=False)
    # WCC_Paycheck Data for 2025
    WCC_2025 = psr.filter_dataframe(df=WCC_stubs,
                                    column="pay_end_date",
                                    search="2025",
                                    mode="year_value")
    # WCC_Paycheck Data for 2026
    WCC_2026 = psr.filter_dataframe(df=WCC_stubs,
                                column="pay_end_date",
                                search="2026",
                                mode="year_value")
    #Inteface outputs in CSV format
    WCC_str = "Whatcom Community College"

    psr.Interface_Block(WCC_str, WCC_2025).report(as_csv=True)
    psr.Interface_Block(WCC_str, WCC_2026).report(as_csv=True)

""" NFCU HANDLING """
if run_NFCU:
    transactions = psr.NFCU_Transactions("data/NFCU/transactions", show=False)
    transactions.clip("Savings")
    transactions.present("Checking")