from glitch.repair.interactive.delta_p import *

delta_p_puppet = PSeq(
    lhs=PSkip(),
    rhs=PSeq(
        lhs=PSeq(
            lhs=PSeq(
                lhs=PLet(
                    id="state-2",
                    expr=PEConst(const=PStr(value="present")),
                    label=2,
                    body=PIf(
                        pred=PEBinOP(
                            op=PEq(),
                            lhs=PEVar(id="state-2"),
                            rhs=PEConst(const=PStr(value="present")),
                        ),
                        cons=PCreate(
                            path=PEConst(
                                const=PStr(
                                    value="/var/www/customers/public_html/index.php"
                                )
                            )
                        ),
                        alt=PIf(
                            pred=PEBinOP(
                                op=PEq(),
                                lhs=PEVar(id="state-2"),
                                rhs=PEConst(const=PStr(value="absent")),
                            ),
                            cons=PRm(
                                path=PEConst(
                                    const=PStr(
                                        value="/var/www/customers/public_html/index.php"
                                    )
                                )
                            ),
                            alt=PIf(
                                pred=PEBinOP(
                                    op=PEq(),
                                    lhs=PEVar(id="state-2"),
                                    rhs=PEConst(const=PStr(value="directory")),
                                ),
                                cons=PMkdir(
                                    path=PEConst(
                                        const=PStr(
                                            value="/var/www/customers/public_html/index.php"
                                        )
                                    )
                                ),
                                alt=PSkip(),
                            ),
                        ),
                    ),
                ),
                rhs=PLet(
                    id="content-1",
                    expr=PEConst(
                        const=PStr(
                            value="<html><body><h1>Hello World</h1></body></html>"
                        )
                    ),
                    label=1,
                    body=PWrite(
                        path=PEConst(
                            const=PStr(value="/var/www/customers/public_html/index.php")
                        ),
                        content=PEVar(id="content-1"),
                    ),
                ),
            ),
            rhs=PLet(
                id="owner-4",
                expr=PEConst(const=PStr(value="web_admin")),
                label=4,
                body=PChown(
                    path=PEConst(
                        const=PStr(value="/var/www/customers/public_html/index.php")
                    ),
                    owner=PEVar(id="owner-4"),
                ),
            ),
        ),
        rhs=PLet(
            id="mode-3",
            expr=PEConst(const=PStr(value="0755")),
            label=3,
            body=PChmod(
                path=PEConst(
                    const=PStr(value="/var/www/customers/public_html/index.php")
                ),
                mode=PEVar(id="mode-3"),
            ),
        ),
    ),
)


delta_p_puppet_2 = PSeq(
    lhs=PSkip(),
    rhs=PSeq(
        lhs=PSeq(
            lhs=PSeq(
                lhs=PLet(
                    id="state-0",
                    expr=PEConst(const=PStr(value="absent")),
                    label=0,
                    body=PIf(
                        pred=PEBinOP(
                            op=PEq(),
                            lhs=PEVar(id="state-0"),
                            rhs=PEConst(const=PStr(value="present")),
                        ),
                        cons=PCreate(
                            path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d"))
                        ),
                        alt=PIf(
                            pred=PEBinOP(
                                op=PEq(),
                                lhs=PEVar(id="state-0"),
                                rhs=PEConst(const=PStr(value="absent")),
                            ),
                            cons=PRm(
                                path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d"))
                            ),
                            alt=PIf(
                                pred=PEBinOP(
                                    op=PEq(),
                                    lhs=PEVar(id="state-0"),
                                    rhs=PEConst(const=PStr(value="directory")),
                                ),
                                cons=PMkdir(
                                    path=PEConst(
                                        const=PStr(value="/usr/sbin/policy-rc.d")
                                    )
                                ),
                                alt=PSkip(),
                            ),
                        ),
                    ),
                ),
                rhs=PLet(
                    id="sketched-content-1",
                    expr=PEUndef(),
                    label=1,
                    body=PWrite(
                        path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                        content=PEVar(id="sketched-content-1"),
                    ),
                ),
            ),
            rhs=PLet(
                id="sketched-owner-2",
                expr=PEUndef(),
                label=2,
                body=PChown(
                    path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                    owner=PEVar(id="sketched-owner-2"),
                ),
            ),
        ),
        rhs=PLet(
            id="sketched-mode-3",
            expr=PEUndef(),
            label=3,
            body=PChmod(
                path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                mode=PEVar(id="sketched-mode-3"),
            ),
        ),
    ),
)


delta_p_puppet_if = PSeq(
    lhs=PSkip(),
    rhs=PIf(
        pred=PEVar(id="dejavu-condition-2"),
        cons=PSeq(
            lhs=PSkip(),
            rhs=PSeq(
                lhs=PSeq(
                    lhs=PSeq(
                        lhs=PLet(
                            id="state-0",
                            expr=PEConst(const=PStr(value="absent")),
                            label=0,
                            body=PIf(
                                pred=PEBinOP(
                                    op=PEq(),
                                    lhs=PEVar(id="state-0"),
                                    rhs=PEConst(const=PStr(value="present")),
                                ),
                                cons=PCreate(
                                    path=PEConst(
                                        const=PStr(value="/usr/sbin/policy-rc.d")
                                    )
                                ),
                                alt=PIf(
                                    pred=PEBinOP(
                                        op=PEq(),
                                        lhs=PEVar(id="state-0"),
                                        rhs=PEConst(const=PStr(value="absent")),
                                    ),
                                    cons=PRm(
                                        path=PEConst(
                                            const=PStr(value="/usr/sbin/policy-rc.d")
                                        )
                                    ),
                                    alt=PIf(
                                        pred=PEBinOP(
                                            op=PEq(),
                                            lhs=PEVar(id="state-0"),
                                            rhs=PEConst(const=PStr(value="directory")),
                                        ),
                                        cons=PMkdir(
                                            path=PEConst(
                                                const=PStr(
                                                    value="/usr/sbin/policy-rc.d"
                                                )
                                            )
                                        ),
                                        alt=PSkip(),
                                    ),
                                ),
                            ),
                        ),
                        rhs=PLet(
                            id="sketched-content-2",
                            expr=PEUndef(),
                            label=2,
                            body=PWrite(
                                path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                                content=PEVar(id="sketched-content-2"),
                            ),
                        ),
                    ),
                    rhs=PLet(
                        id="sketched-owner-3",
                        expr=PEUndef(),
                        label=3,
                        body=PChown(
                            path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                            owner=PEVar(id="sketched-owner-3"),
                        ),
                    ),
                ),
                rhs=PLet(
                    id="sketched-mode-4",
                    expr=PEUndef(),
                    label=4,
                    body=PChmod(
                        path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                        mode=PEVar(id="sketched-mode-4"),
                    ),
                ),
            ),
        ),
        alt=PIf(
            pred=PEVar(id="dejavu-condition-1"),
            cons=PSeq(
                lhs=PSkip(),
                rhs=PSeq(
                    lhs=PSeq(
                        lhs=PSeq(
                            lhs=PLet(
                                id="state-1",
                                expr=PEConst(const=PStr(value="present")),
                                label=1,
                                body=PIf(
                                    pred=PEBinOP(
                                        op=PEq(),
                                        lhs=PEVar(id="state-1"),
                                        rhs=PEConst(const=PStr(value="present")),
                                    ),
                                    cons=PCreate(
                                        path=PEConst(
                                            const=PStr(value="/usr/sbin/policy-rc.d")
                                        )
                                    ),
                                    alt=PIf(
                                        pred=PEBinOP(
                                            op=PEq(),
                                            lhs=PEVar(id="state-1"),
                                            rhs=PEConst(const=PStr(value="absent")),
                                        ),
                                        cons=PRm(
                                            path=PEConst(
                                                const=PStr(
                                                    value="/usr/sbin/policy-rc.d"
                                                )
                                            )
                                        ),
                                        alt=PIf(
                                            pred=PEBinOP(
                                                op=PEq(),
                                                lhs=PEVar(id="state-1"),
                                                rhs=PEConst(
                                                    const=PStr(value="directory")
                                                ),
                                            ),
                                            cons=PMkdir(
                                                path=PEConst(
                                                    const=PStr(
                                                        value="/usr/sbin/policy-rc.d"
                                                    )
                                                )
                                            ),
                                            alt=PSkip(),
                                        ),
                                    ),
                                ),
                            ),
                            rhs=PLet(
                                id="sketched-content-5",
                                expr=PEUndef(),
                                label=5,
                                body=PWrite(
                                    path=PEConst(
                                        const=PStr(value="/usr/sbin/policy-rc.d")
                                    ),
                                    content=PEVar(id="sketched-content-5"),
                                ),
                            ),
                        ),
                        rhs=PLet(
                            id="sketched-owner-6",
                            expr=PEUndef(),
                            label=6,
                            body=PChown(
                                path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                                owner=PEVar(id="sketched-owner-6"),
                            ),
                        ),
                    ),
                    rhs=PLet(
                        id="sketched-mode-7",
                        expr=PEUndef(),
                        label=7,
                        body=PChmod(
                            path=PEConst(const=PStr(value="/usr/sbin/policy-rc.d")),
                            mode=PEVar(id="sketched-mode-7"),
                        ),
                    ),
                ),
            ),
            alt=PSkip(),
        ),
    ),
)


delta_p_puppet_default_state = PSeq(
    lhs=PSkip(),
    rhs=PSeq(
        lhs=PSeq(
            lhs=PSeq(
                lhs=PLet(
                    id="sketched-state-4",
                    expr=PEConst(const=PStr(value="present")),
                    label=4,
                    body=PIf(
                        pred=PEBinOP(
                            op=PEq(),
                            lhs=PEVar(id="sketched-state-4"),
                            rhs=PEConst(const=PStr(value="present")),
                        ),
                        cons=PCreate(
                            path=PEConst(const=PStr(value="/root/.ssh/config"))
                        ),
                        alt=PIf(
                            pred=PEBinOP(
                                op=PEq(),
                                lhs=PEVar(id="sketched-state-4"),
                                rhs=PEConst(const=PStr(value="absent")),
                            ),
                            cons=PRm(
                                path=PEConst(const=PStr(value="/root/.ssh/config"))
                            ),
                            alt=PIf(
                                pred=PEBinOP(
                                    op=PEq(),
                                    lhs=PEVar(id="sketched-state-4"),
                                    rhs=PEConst(const=PStr(value="directory")),
                                ),
                                cons=PMkdir(
                                    path=PEConst(const=PStr(value="/root/.ssh/config"))
                                ),
                                alt=PSkip(),
                            ),
                        ),
                    ),
                ),
                rhs=PLet(
                    id="content-0",
                    expr=PEConst(
                        const=PStr(value="template('fuel/root_ssh_config.erb')")
                    ),
                    label=0,
                    body=PWrite(
                        path=PEConst(const=PStr(value="/root/.ssh/config")),
                        content=PEVar(id="content-0"),
                    ),
                ),
            ),
            rhs=PLet(
                id="owner-1",
                expr=PEConst(const=PStr(value="root")),
                label=1,
                body=PChown(
                    path=PEConst(const=PStr(value="/root/.ssh/config")),
                    owner=PEVar(id="owner-1"),
                ),
            ),
        ),
        rhs=PLet(
            id="mode-3",
            expr=PEConst(const=PStr(value="0600")),
            label=3,
            body=PChmod(
                path=PEConst(const=PStr(value="/root/.ssh/config")),
                mode=PEVar(id="mode-3"),
            ),
        ),
    ),
)
