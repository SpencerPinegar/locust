import os
import sys
import shlex
import logging

from app.Utils.environment_wrapper import RecAPIEnvironmentWrapper as APIWrap


def run_locust(options):
    import gevent
    import socket
    import signal
    import locust

    from locust import events, runners, web
    from locust.log import console_logger, setup_logging
    from locust.runners import LocalLocustRunner, MasterLocustRunner, SlaveLocustRunner
    from locust.stats import (print_error_report, print_percentile_stats, print_stats,
                              stats_printer, stats_writer, write_stat_csvs)
    from locust.main import find_locustfile, load_locustfile
    version = locust.__version__
    locust_options = options
    # setup logging
    setup_logging(locust_options.loglevel, locust_options.logfile)
    logger = logging.getLogger(__name__)

    locustfile = find_locustfile(locust_options.locustfile)

    if not locustfile:
        logger.error(
            "Could not find any locustfile! Ensure file ends in '.py' and see --help for available options.")
        sys.exit(1)

    if locustfile == "locust.py":
        logger.error("The locustfile must not be named `locust.py`. Please rename the file and try again.")
        sys.exit(1)

    docstring, locusts = load_locustfile(locustfile)

    if not locusts:
        logger.error("No Locust class found!")
        sys.exit(1)

    locust_classes = list(locusts.values())

    if not locust_options.no_web and not locust_options.slave:
        # spawn web greenlet
        logger.info("Starting web monitor at %s:%s" % (locust_options.web_host or "*", locust_options.port))
        main_greenlet = gevent.spawn(web.start, locust_classes, locust_options)

    if not locust_options.master and not locust_options.slave:
        runners.locust_runner = LocalLocustRunner(locust_classes, locust_options)
        # spawn client spawning/hatching greenlet
        if locust_options.no_web:
            runners.locust_runner.start_hatching(wait=True)
            main_greenlet = runners.locust_runner.greenlet

    elif locust_options.master:
        runners.locust_runner = MasterLocustRunner(locust_classes, locust_options)

    elif locust_options.slave:
        try:
            runners.locust_runner = SlaveLocustRunner(locust_classes, locust_options)
            main_greenlet = runners.locust_runner.greenlet
        except socket.error as e:
            logger.error("Failed to connect to the Locust master: %s", e)
            sys.exit(-1)

    if not locust_options.only_summary and (locust_options.print_stats or (locust_options.no_web and not locust_options.slave)):
        # spawn stats printing greenlet
        gevent.spawn(stats_printer)

    if locust_options.csvfilebase:
        gevent.spawn(stats_writer, locust_options.csvfilebase)

    def shutdown(code=0):
        """
        Shut down locust by firing quitting event, printing/writing stats and exiting
        """
        logger.info("Shutting down (exit code %s), bye." % code)

        logger.info("Cleaning up runner...")
        if runners.locust_runner is not None:
            runners.locust_runner.quit()
        logger.info("Running teardowns...")
        events.quitting.fire(reverse=True)
        print_stats(runners.locust_runner.request_stats)
        print_percentile_stats(runners.locust_runner.request_stats)
        if locust_options.csvfilebase:
            write_stat_csvs(locust_options.csvfilebase)
        print_error_report()
        sys.exit(code)

    # install SIGTERM handler
    def sig_term_handler():
        logger.info("Got SIGTERM signal")
        shutdown(0)

    gevent.signal(signal.SIGTERM, sig_term_handler)

    try:
        logger.info("Starting Locust %s" % version)
        main_greenlet.join()
        code = 0
        if len(runners.locust_runner.errors):
            code = 1
        shutdown(code=code)
    except KeyboardInterrupt as e:
        shutdown(0)



def create_master_options(name_space_options):
    locust_path = "locust"  # self.__get_locust_file_dir()

    master_arg_string = "{locust} -f {master_file} -H {l_host} --master --master-bind-host={mb_host} --master-bind-port={mb_port}".format(
        locust=locust_path, master_file=name_space_options.locustfile, l_host=name_space_options.host,
        mb_host=name_space_options.master_bind_host, mb_port=name_space_options.master_bind_port
    )
    if name_space_options.csvfilebase:
        master_arg_string = "{master_arg_string} --csv={file_name}".format(master_arg_string=master_arg_string,
                                                                           file_name=name_space_options.csvfilebase)
    master_arg_string = "{master_arg_string} --loglevel={loglevel}".format(master_arg_string=master_arg_string,
                                                                               loglevel=name_space_options.loglevel)
    return shlex.split(master_arg_string)


def create_slave_options(name_space_options):
    locust_path = "locust"  # self.__get_locust_file_dir()

    slave_arg_string = "{locust} -f {slave_file} -H {l_host} --slave --master-host={m_host} --master-port={m_port}".format(
        locust=locust_path, slave_file=name_space_options.locustfile, l_host=name_space_options.host,
        m_host=name_space_options.master_host, m_port=name_space_options.master_port
    )
    return shlex.split(slave_arg_string)


def create_undistributed_options(name_space_options):
    locust_path = "locust"  # self.__get_locust_file_dir()

    undis_arg_string = "{locust} -f {undis_file} -H {l_host} ".format(
        locust=locust_path, undis_file=name_space_options.locustfile, l_host=name_space_options.host,
    )
    if name_space_options.csvfilebase:
        undis_arg_string = "{undis_arg_string} --csv={file_name}".format(undis_arg_string=undis_arg_string,
                                                                         file_name=name_space_options.csvfilebase)
    undis_arg_string = "{undis_arg_string} --loglevel={loglevel}".format(undis_arg_string=undis_arg_string,
                                                                         loglevel=name_space_options.loglevel)
    return shlex.split(undis_arg_string)