#!/bin/sh -e

create_host_router () {
    n="$1"
    echo "creating router R$n and host H$n"
    sudo ip netns add R$n
    sudo ip netns add H$n
    sudo ip link add H$n-eth0 type veth peer name R$n-eth0
    sudo ip link set H$n-eth0 netns H$n
    sudo ip link set R$n-eth0 netns R$n

    sudo ip netns exec H$n ip addr add 10.0.$n.1/24 dev H$n-eth0
    sudo ip netns exec R$n ip addr add 10.0.$n.254/24 dev R$n-eth0
    sudo ip netns exec H$n ip link set H$n-eth0 up
    sudo ip netns exec R$n ip link set R$n-eth0 up

    sudo ip netns exec H$n ip route add default via 10.0.$n.254 dev H$n-eth0

    sudo ip netns exec R$n sysctl net.ipv4.ip_forward=1
    # enable ping for the world on both the host and the router.
    # https://docs.kernel.org/networking/ip-sysctl.html#ip-sysctl
    sudo ip netns exec R$n sysctl net.ipv4.ping_group_range='0 4294967294'
    sudo ip netns exec H$n sysctl net.ipv4.ping_group_range='0 4294967294'
}

delete_host_router () {
    n="$1"
    echo "deleting router R$n and host H$n"
    sudo ip netns delete R$n
    sudo ip netns delete H$n
}

link_count=1

create_link () {
    if [ $1 -gt $2 ]
    then
       u=$2
       v=$1
    else
       u=$1
       v=$2
    fi
    shift
    shift
    echo "creating link R$u -- R$v  $@"
    sudo ip link add R$u-eth$v type veth peer name R$v-eth$u
    sudo ip link set R$u-eth$v netns R$u
    sudo ip link set R$v-eth$u netns R$v
    sudo ip netns exec R$u ifconfig R$u-eth$v 10.$u.$v.$u netmask 255.255.255.0
    sudo ip netns exec R$v ifconfig R$v-eth$u 10.$u.$v.$v netmask 255.255.255.0

    if [ -n "$1" ]
    then
	sudo ip netns exec R$u tc qdisc add dev R$u-eth$v root netem $@
	sudo ip netns exec R$v tc qdisc add dev R$v-eth$u root netem $@
    fi
}

configure_link () {
    if [ $1 -gt $2 ]
    then
       u=$2
       v=$1
    else
       u=$1
       v=$2
    fi
    echo "configuring link R$u -- R$v"
    if [ -n "$1" ]
    then
	sudo ip netns exec R$u tc qdisc replace dev R$u-eth$v root netem "$@"
	sudo ip netns exec R$v tc qdisc replace dev R$v-eth$u root netem "$@"
    else
	sudo ip netns exec R$u tc qdisc remove dev R$u-eth$v root
	sudo ip netns exec R$v tc qdisc remove dev R$v-eth$u root
    fi
}

configure_link () {
    if [ $1 -gt $2 ]
    then
       u=$2
       v=$1
    else
       u=$1
       v=$2
    fi
    shift
    shift
    case "$1" in
	show )
	    echo "traffic control on link R$u -- R$v:"
	    sudo ip netns exec R$u tc -p qdisc show dev R$u-eth$v
	    sudo ip netns exec R$v tc qdisc show dev R$v-eth$u
	    ;;
	reset )
	    echo "removing traffic control on link R$u -- R$v"
	    sudo ip netns exec R$u tc qdisc delete dev R$u-eth$v root
	    sudo ip netns exec R$v tc qdisc delete dev R$v-eth$u root
	    ;;
	* )
	    echo "changing traffic control on link R$u -- R$v"
	    sudo ip netns exec R$u tc qdisc replace dev R$u-eth$v root netem "$@"
	    sudo ip netns exec R$v tc qdisc replace dev R$v-eth$u root netem "$@"
	    ;;
    esac
}

add_fwd_rule () {
    echo "fwd rule on R$1: send to H$2 via R$3"
    a=$1
    b=$3
    if [ $a -gt $b ]
    then
       u=$b
       v=$a
    else
       u=$a
       v=$b
    fi
    dst=10.0.$2.0/24
    sudo ip netns exec R$a ip route add $dst via 10.$u.$v.$b dev R$a-eth$b
}

run_terminal_host () {
    echo "starting shell on host H$1"
    echo "$USER"
    exec sudo ip netns exec H$1 sudo -u "$USER" bash -c "exec bash -i <<< \"PS1='H$1> '; exec </dev/tty\""
}

run_terminal () {
    echo "starting shell in namespace $1"
    exec sudo ip netns exec $1 sudo -u "$USER" bash -c "exec bash -i <<< \"PS1='$1> '; exec </dev/tty\""
}

case "$1" in
    off | down )
	delete_host_router 1
	delete_host_router 2
	;;
    1 | 2 )
	run_terminal_host "$1"
	;;
    H[0-9]* | R[0-9]* )
	run_terminal "$1"
	;;
    link )
	shift
	configure_link 1 2 "$@"
	;;
    "" | on | up )
	create_host_router 1
	create_host_router 2
	#
	create_link 1 2 "delay 50ms 30ms loss 5% rate 1mbit"
	#
	add_fwd_rule 1 2 2
	add_fwd_rule 2 1 1
	;;
esac
